import os
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, current_app, abort
from flask_login import login_user, login_required, logout_user, current_user
from models import Company, Job, User, JobApplication
from extensions import db
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from forms import CompanyForm, JobForm, JobApplicationForm, RegistrationForm
import logging

main = Blueprint('main', __name__)

@main.route('/')
def index():
    companies = Company.query.all()
    logging.info(f"Retrieved {len(companies)} companies for index page")
    return render_template('index.html', companies=companies)

@main.route('/company/<int:company_id>')
def company(company_id):
    company = Company.query.get_or_404(company_id)
    logging.info(f"Retrieved company {company.name} (ID: {company.id}) with {len(company.jobs)} job listings")
    return render_template('company.html', company=company)

@main.route('/search')
def search():
    query = request.args.get('q', '')
    jobs = Job.query.filter(Job.title.ilike(f'%{query}%')).all()
    logging.info(f"Search query: '{query}' returned {len(jobs)} job listings")
    return render_template('search.html', jobs=jobs, query=query)

@main.route('/api/search')
def api_search():
    query = request.args.get('q', '')
    jobs = Job.query.filter(Job.title.ilike(f'%{query}%')).all()
    logging.info(f"API search query: '{query}' returned {len(jobs)} job listings")
    return jsonify([{
        'id': job.id,
        'title': job.title,
        'company': job.company.name,
        'company_id': job.company_id,
        'description': job.description
    } for job in jobs])

@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        logging.info(f"Login attempt for username: {username}")
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            logging.info(f"User {username} logged in successfully")
            flash('Logged in successfully.', 'success')
            return redirect(url_for('main.index'))
        else:
            logging.warning(f"Invalid login attempt for user: {username}")
            flash('Invalid username or password.', 'error')
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
    return render_template('profile.html')

@main.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
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
            db.session.add(new_user)
            db.session.commit()
            logging.info(f"New user registered: {new_user.username}, is_employer: {new_user.is_employer}")
            flash('Registered successfully. Please log in.', 'success')
            return redirect(url_for('main.login'))

    return render_template('register.html', form=form)

@main.route('/apply/<int:job_id>', methods=['GET', 'POST'])
@login_required
def apply_for_job(job_id):
    job = Job.query.get_or_404(job_id)
    form = JobApplicationForm()

    if current_user.is_employer:
        flash('Employers cannot apply for jobs.', 'error')
        return redirect(url_for('main.company', company_id=job.company_id))

    if form.validate_on_submit():
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
            db.session.add(application)
            db.session.commit()
            logging.info(f"New job application submitted: Job ID {job_id}, User ID {current_user.id}")
            flash('Your application has been submitted successfully.', 'success')
        return redirect(url_for('main.profile'))

    return render_template('apply.html', job=job, form=form)

@main.route('/application/<int:application_id>')
@login_required
def view_application(application_id):
    application = JobApplication.query.get_or_404(application_id)
    if application.user_id != current_user.id:
        abort(403)  # Forbidden access
    return render_template('view_application.html', application=application)

@main.route('/admin')
@login_required
def admin_panel():
    if not current_user.is_admin:
        abort(403)  # Forbidden access
    companies = Company.query.all()
    jobs = Job.query.all()
    job_count = len(jobs)
    logging.info(f"Admin panel accessed. Current job count: {job_count}")
    return render_template('admin/panel.html', companies=companies, jobs=jobs, job_count=job_count)

@main.route('/admin/company/add', methods=['GET', 'POST'])
@login_required
def admin_add_company():
    if not current_user.is_admin:
        abort(403)  # Forbidden access
    form = CompanyForm()
    if form.validate_on_submit():
        new_company = Company(name=form.name.data, description=form.description.data)
        if form.image.data:
            image = form.image.data
            filename = secure_filename(image.filename)
            image_path = os.path.join(current_app.root_path, 'static/uploads', filename)
            image.save(image_path)
            new_company.image = filename
        db.session.add(new_company)
        db.session.commit()
        logging.info(f"New company added: {new_company.name}")
        flash('Company added successfully.', 'success')
        return redirect(url_for('main.admin_panel'))
    return render_template('admin/company_form.html', form=form, title='Add Company')

@main.route('/admin/company/edit/<int:company_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_company(company_id):
    if not current_user.is_admin:
        abort(403)  # Forbidden access
    company = Company.query.get_or_404(company_id)
    form = CompanyForm(obj=company)
    if form.validate_on_submit():
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
        db.session.commit()
        logging.info(f"Company updated: {company.name}")
        flash('Company updated successfully.', 'success')
        return redirect(url_for('main.admin_panel'))
    return render_template('admin/company_form.html', form=form, title='Edit Company')

@main.route('/admin/job/add', methods=['GET', 'POST'])
@login_required
def admin_add_job():
    if not current_user.is_admin:
        abort(403)  # Forbidden access
    form = JobForm()
    form.company_id = request.args.get('company_id')
    if form.validate_on_submit():
        new_job = Job(
            title=form.title.data,
            description=form.description.data,
            requirements=form.requirements.data,
            company_id=form.company_id
        )
        db.session.add(new_job)
        db.session.commit()
        logging.info(f"New job added: {new_job.title} for company ID {new_job.company_id}")
        flash('Job added successfully.', 'success')
        return redirect(url_for('main.admin_panel'))
    return render_template('admin/job_form.html', form=form, title='Add Job')

@main.route('/admin/job/edit/<int:job_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_job(job_id):
    if not current_user.is_admin:
        abort(403)  # Forbidden access
    job = Job.query.get_or_404(job_id)
    form = JobForm(obj=job)
    if form.validate_on_submit():
        job.title = form.title.data
        job.description = form.description.data
        job.requirements = form.requirements.data
        db.session.commit()
        logging.info(f"Job updated: {job.title} (ID: {job.id})")
        flash('Job updated successfully.', 'success')
        return redirect(url_for('main.admin_panel'))
    return render_template('admin/job_form.html', form=form, title='Edit Job')