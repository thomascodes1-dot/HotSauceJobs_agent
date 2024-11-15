import os
import secrets
from PIL import Image
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, current_app, abort, session, g
from flask_login import login_user, login_required, logout_user, current_user
from models import Company, Job, User, JobApplication
from extensions import db
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from forms import CompanyForm, JobForm, JobApplicationForm, RegistrationForm, ProfileEditForm
import logging
from sqlalchemy import desc
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timedelta

main = Blueprint('main', __name__)

@main.before_request
def before_request():
    session.permanent = True
    current_app.permanent_session_lifetime = timedelta(minutes=30)
    session.modified = True
    g.db = db.session()

@main.teardown_request
def teardown_request(exception):
    if hasattr(g, 'db'):
        g.db.close()

@main.route('/keep-alive')
def keep_alive():
    return jsonify({"status": "ok"}), 200

@main.errorhandler(404)
def page_not_found(e):
    current_app.logger.error(f"404 error: {str(e)}")
    return render_template('errors/404.html'), 404

@main.errorhandler(500)
def internal_server_error(e):
    current_app.logger.error(f"500 error: {str(e)}")
    return render_template('errors/500.html'), 500

@main.route('/')
def index():
    try:
        companies = g.db.query(Company, User.profile_picture).outerjoin(User, Company.id == User.id).all()
        current_app.logger.info(f"Retrieved {len(companies)} companies for index page")
        return render_template('index.html', companies=companies)
    except SQLAlchemyError as e:
        current_app.logger.error(f"Database error in index route: {str(e)}")
        flash('An error occurred while loading the page. Please try again.', 'error')
        return render_template('index.html', companies=[])

@main.route('/company/<int:company_id>')
def company(company_id):
    try:
        company = Company.query.get_or_404(company_id)
        owner = User.query.get(company_id)
        profile_picture = owner.profile_picture if owner else None
        current_app.logger.info(f"Retrieved company {company.name} (ID: {company.id}) with {len(company.jobs)} job listings")
        return render_template('company.html', company=company, profile_picture=profile_picture)
    except SQLAlchemyError as e:
        current_app.logger.error(f"Database error in company route: {str(e)}")
        flash('An error occurred while loading the company page. Please try again.', 'error')
        return redirect(url_for('main.index'))

@main.route('/search')
def search():
    try:
        query = request.args.get('q', '')
        jobs = Job.query.filter(Job.title.ilike(f'%{query}%')).all()
        current_app.logger.info(f"Search query: '{query}' returned {len(jobs)} job listings")
        return render_template('search.html', jobs=jobs, query=query)
    except SQLAlchemyError as e:
        current_app.logger.error(f"Database error in search route: {str(e)}")
        flash('An error occurred while searching. Please try again.', 'error')
        return render_template('search.html', jobs=[], query=query)

@main.route('/api/search')
def api_search():
    try:
        query = request.args.get('q', '')
        jobs = Job.query.filter(Job.title.ilike(f'%{query}%')).all()
        current_app.logger.info(f"API search query: '{query}' returned {len(jobs)} job listings")
        return jsonify([{
            'id': job.id,
            'title': job.title,
            'company': job.company.name,
            'company_id': job.company_id,
            'description': job.description
        } for job in jobs])
    except SQLAlchemyError as e:
        current_app.logger.error(f"Database error in API search route: {str(e)}")
        return jsonify({'error': 'An error occurred while searching'}), 500

@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        current_app.logger.info(f"Login attempt for username: {username}")
        try:
            user = User.query.filter_by(username=username).first()
            if user and user.check_password(password):
                login_user(user)
                current_app.logger.info(f"User {username} logged in successfully")
                flash('Logged in successfully.', 'success')
                return redirect(url_for('main.index'))
            else:
                current_app.logger.warning(f"Invalid login attempt for user: {username}")
                flash('Invalid username or password.', 'error')
        except SQLAlchemyError as e:
            current_app.logger.error(f"Database error in login route: {str(e)}")
            flash('An error occurred. Please try again.', 'error')
    return render_template('login.html')

@main.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('main.index'))

@main.route('/profile')
@login_required
def profile():
    try:
        if current_user.is_employer:
            jobs = Job.query.filter_by(company_id=current_user.id).all()
            return render_template('profile.html', jobs=jobs)
        else:
            return render_template('profile.html')
    except SQLAlchemyError as e:
        current_app.logger.error(f"Database error in profile route: {str(e)}")
        flash('An error occurred while loading your profile. Please try again.', 'error')
        return redirect(url_for('main.index'))

@main.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = ProfileEditForm(obj=current_user)
    if form.validate_on_submit():
        try:
            current_user.username = form.username.data
            if current_user.is_employer:
                current_user.company_name = form.company_name.data
                current_user.company_description = form.company_description.data
            
            if form.profile_picture.data:
                picture_file = save_picture(form.profile_picture.data)
                current_user.profile_picture = picture_file
                current_app.logger.info(f"Updated profile picture for user {current_user.username}: {picture_file}")
            
            g.db.commit()
            flash('Your profile has been updated!', 'success')
            return redirect(url_for('main.profile'))
        except SQLAlchemyError as e:
            g.db.rollback()
            current_app.logger.error(f"Database error in edit_profile route: {str(e)}")
            flash('An error occurred while updating your profile. Please try again.', 'error')
    
    return render_template('edit_profile.html', form=form)

def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(current_app.root_path, 'static', 'profile_pics')
    
    os.makedirs(picture_path, exist_ok=True)
    
    picture_path = os.path.join(picture_path, picture_fn)
    
    output_size = (150, 150)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)
    
    current_app.logger.info(f"Saved profile picture: {picture_fn}")
    return picture_fn

@main.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            user = User.query.filter_by(username=form.username.data).first()
            if user:
                flash('Username already exists.', 'error')
            else:
                new_user = User(
                    username=form.username.data,
                    is_employer=form.is_employer.data,
                    company_name=form.company_name.data if form.is_employer.data else None,
                    company_description=form.company_description.data if form.is_employer.data else None
                )
                new_user.set_password(form.password.data)
                g.db.add(new_user)
                
                if new_user.is_employer:
                    new_company = Company(name=form.company_name.data, description=form.company_description.data)
                    g.db.add(new_company)
                    g.db.flush()
                    new_user.id = new_company.id
                
                g.db.commit()
                current_app.logger.info(f"New user registered: {new_user.username}, is_employer: {new_user.is_employer}")
                flash('Registered successfully. Please log in.', 'success')
                return redirect(url_for('main.login'))
        except SQLAlchemyError as e:
            g.db.rollback()
            current_app.logger.error(f"Database error in register route: {str(e)}")
            flash('An error occurred during registration. Please try again.', 'error')

    return render_template('register.html', form=form)

@main.route('/apply/<int:job_id>', methods=['GET', 'POST'])
@login_required
def apply_for_job(job_id):
    job = Job.query.get_or_404(job_id)
    form = JobApplicationForm()

    if form.validate_on_submit():
        try:
            existing_application = JobApplication.query.filter_by(job_id=job_id, user_id=current_user.id).first()
            if existing_application:
                flash('You have already applied for this job.', 'warning')
            else:
                cover_letter = form.cover_letter.data
                resume = form.resume.data
                filename = secure_filename(resume.filename)
                resume_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                resume.save(resume_path)

                application = JobApplication(
                    job_id=job_id,
                    user_id=current_user.id,
                    cover_letter=cover_letter,
                    resume_filename=filename
                )
                g.db.add(application)
                g.db.commit()
                current_app.logger.info(f"New job application submitted: Job ID {job_id}, User ID {current_user.id}")
                flash('Your application has been submitted successfully.', 'success')
            return redirect(url_for('main.profile'))
        except SQLAlchemyError as e:
            g.db.rollback()
            current_app.logger.error(f"Database error in apply_for_job route: {str(e)}")
            flash('An error occurred while submitting your application. Please try again.', 'error')

    return render_template('apply.html', job=job, form=form)

@main.route('/application/<int:application_id>')
@login_required
def view_application(application_id):
    try:
        application = JobApplication.query.get_or_404(application_id)
        if application.user_id != current_user.id:
            abort(403)
        return render_template('view_application.html', application=application)
    except SQLAlchemyError as e:
        current_app.logger.error(f"Database error in view_application route: {str(e)}")
        flash('An error occurred while loading the application. Please try again.', 'error')
        return redirect(url_for('main.profile'))

@main.route('/employer/applications/<int:job_id>')
@login_required
def employer_view_applications(job_id):
    if not current_user.is_employer:
        abort(403)
    
    try:
        job = Job.query.get_or_404(job_id)
        
        if job.company_id != current_user.id:
            abort(403)
        
        page = request.args.get('page', 1, type=int)
        status_filter = request.args.get('status', 'all')
        per_page = 10

        query = JobApplication.query.filter_by(job_id=job_id)

        if status_filter != 'all':
            query = query.filter_by(status=status_filter)

        applications = query.order_by(desc(JobApplication.created_at)).paginate(page=page, per_page=per_page, error_out=False)
        
        return render_template('employer_applications.html', job=job, applications=applications, status_filter=status_filter)
    except SQLAlchemyError as e:
        current_app.logger.error(f"Database error in employer_view_applications route: {str(e)}")
        flash('An error occurred while loading the applications. Please try again.', 'error')
        return redirect(url_for('main.profile'))

@main.route('/employer/update_application/<int:application_id>', methods=['POST'])
@login_required
def update_application_status(application_id):
    if not current_user.is_employer:
        abort(403)
    
    try:
        application = JobApplication.query.get_or_404(application_id)
        
        if application.job.company_id != current_user.id:
            abort(403)
        
        new_status = request.form.get('status')
        if new_status in ['pending', 'reviewed', 'accepted', 'rejected']:
            application.status = new_status
            g.db.commit()
            flash('Application status updated successfully.', 'success')
        else:
            flash('Invalid status.', 'error')
        
        return redirect(url_for('main.employer_view_applications', job_id=application.job_id))
    except SQLAlchemyError as e:
        g.db.rollback()
        current_app.logger.error(f"Database error in update_application_status route: {str(e)}")
        flash('An error occurred while updating the application status. Please try again.', 'error')
        return redirect(url_for('main.employer_view_applications', job_id=application.job_id))

@main.route('/admin')
@login_required
def admin_panel():
    if not current_user.is_admin:
        abort(403)
    try:
        companies = Company.query.all()
        jobs = Job.query.all()
        job_count = len(jobs)
        current_app.logger.info(f"Admin panel accessed. Current job count: {job_count}")
        return render_template('admin/panel.html', companies=companies, jobs=jobs, job_count=job_count)
    except SQLAlchemyError as e:
        current_app.logger.error(f"Database error in admin_panel route: {str(e)}")
        flash('An error occurred while loading the admin panel. Please try again.', 'error')
        return redirect(url_for('main.index'))

@main.route('/admin/company/add', methods=['GET', 'POST'])
@login_required
def admin_add_company():
    if not current_user.is_admin:
        abort(403)
    form = CompanyForm()
    if form.validate_on_submit():
        try:
            new_company = Company(name=form.name.data, description=form.description.data)
            if form.image.data:
                image = form.image.data
                filename = secure_filename(image.filename)
                image_path = os.path.join(current_app.root_path, 'static/uploads', filename)
                image.save(image_path)
                new_company.image = filename
            g.db.add(new_company)
            g.db.commit()
            current_app.logger.info(f"New company added: {new_company.name}")
            flash('Company added successfully.', 'success')
            return redirect(url_for('main.admin_panel'))
        except SQLAlchemyError as e:
            g.db.rollback()
            current_app.logger.error(f"Database error in admin_add_company route: {str(e)}")
            flash('An error occurred while adding the company. Please try again.', 'error')
    return render_template('admin/company_form.html', form=form, title='Add Company')

@main.route('/admin/company/edit/<int:company_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_company(company_id):
    if not current_user.is_admin:
        abort(403)
    company = Company.query.get_or_404(company_id)
    form = CompanyForm(obj=company)
    if form.validate_on_submit():
        try:
            company.name = form.name.data
            company.description = form.description.data
            if form.image.data:
                image = form.image.data
                filename = secure_filename(image.filename)
                image_path = os.path.join(current_app.root_path, 'static/uploads', filename)
                image.save(image_path)
                if company.image:
                    old_image_path = os.path.join(current_app.root_path, 'static/uploads', company.image)
                    if os.path.exists(old_image_path):
                        os.remove(old_image_path)
                company.image = filename
            g.db.commit()
            current_app.logger.info(f"Company updated: {company.name}")
            flash('Company updated successfully.', 'success')
            return redirect(url_for('main.admin_panel'))
        except SQLAlchemyError as e:
            g.db.rollback()
            current_app.logger.error(f"Database error in admin_edit_company route: {str(e)}")
            flash('An error occurred while updating the company. Please try again.', 'error')
    return render_template('admin/company_form.html', form=form, title='Edit Company')

@main.route('/admin/job/add', methods=['GET', 'POST'])
@login_required
def admin_add_job():
    if not current_user.is_admin:
        abort(403)
    form = JobForm()
    form.company_id = request.args.get('company_id')
    if form.validate_on_submit():
        try:
            new_job = Job(
                title=form.title.data,
                description=form.description.data,
                requirements=form.requirements.data,
                company_id=form.company_id
            )
            g.db.add(new_job)
            g.db.commit()
            current_app.logger.info(f"New job added: {new_job.title} for company ID {new_job.company_id}")
            flash('Job added successfully.', 'success')
            return redirect(url_for('main.admin_panel'))
        except SQLAlchemyError as e:
            g.db.rollback()
            current_app.logger.error(f"Database error in admin_add_job route: {str(e)}")
            flash('An error occurred while adding the job. Please try again.', 'error')
    return render_template('admin/job_form.html', form=form, title='Add Job')

@main.route('/admin/job/edit/<int:job_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_job(job_id):
    if not current_user.is_admin:
        abort(403)
    job = Job.query.get_or_404(job_id)
    form = JobForm(obj=job)
    if form.validate_on_submit():
        try:
            job.title = form.title.data
            job.description = form.description.data
            job.requirements = form.requirements.data
            g.db.commit()
            current_app.logger.info(f"Job updated: {job.title} (ID: {job.id})")
            flash('Job updated successfully.', 'success')
            return redirect(url_for('main.admin_panel'))
        except SQLAlchemyError as e:
            g.db.rollback()
            current_app.logger.error(f"Database error in admin_edit_job route: {str(e)}")
            flash('An error occurred while updating the job. Please try again.', 'error')
    return render_template('admin/job_form.html', form=form, title='Edit Job')

@main.route('/admin/job/delete/<int:job_id>', methods=['POST'])
@login_required
def admin_delete_job(job_id):
    if not current_user.is_admin:
        abort(403)
    try:
        job = Job.query.get_or_404(job_id)
        
        JobApplication.query.filter_by(job_id=job_id).delete()
        
        g.db.delete(job)
        g.db.commit()
        
        current_app.logger.info(f"Job deleted successfully: {job.title} (ID: {job.id})")
        flash('Job deleted successfully.', 'success')
    except SQLAlchemyError as e:
        g.db.rollback()
        current_app.logger.error(f"Error deleting job (ID: {job_id}): {str(e)}")
        flash('An error occurred while deleting the job. Please try again.', 'error')
    
    return redirect(url_for('main.admin_panel'))

def get_or_create_company(user):
    company = Company.query.get(user.id)
    if not company:
        company = Company(id=user.id, name=user.company_name, description=user.company_description)
        g.db.add(company)
        g.db.commit()
    return company

@main.route('/post_job', methods=['GET', 'POST'])
@login_required
def post_job():
    if not current_user.is_employer:
        abort(403)
    
    form = JobForm()
    if form.validate_on_submit():
        try:
            company = get_or_create_company(current_user)
            new_job = Job(
                title=form.title.data,
                description=form.description.data,
                requirements=form.requirements.data,
                company_id=company.id
            )
            g.db.add(new_job)
            g.db.commit()
            current_app.logger.info(f"New job posted: {new_job.title} by employer {current_user.username}")
            flash('Job posted successfully.', 'success')
            return redirect(url_for('main.profile'))
        except SQLAlchemyError as e:
            g.db.rollback()
            current_app.logger.error(f"Database error in post_job route: {str(e)}")
            flash('An error occurred while posting the job. Please try again.', 'error')
    
    return render_template('post_job.html', form=form)