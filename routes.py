from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, current_app, abort
from flask_login import login_user, login_required, logout_user, current_user
from models import Company, Job, User, JobApplication
from extensions import db
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from flask_wtf import FlaskForm
from wtforms import TextAreaField, FileField
from wtforms.validators import DataRequired
import os
import logging

main = Blueprint('main', __name__)

class JobApplicationForm(FlaskForm):
    cover_letter = TextAreaField('Cover Letter', validators=[DataRequired()])
    resume = FileField('Resume', validators=[DataRequired()])

@main.route('/')
def index():
    companies = Company.query.all()
    return render_template('index.html', companies=companies)

@main.route('/company/<int:company_id>')
def company(company_id):
    company = Company.query.get_or_404(company_id)
    return render_template('company.html', company=company)

@main.route('/search')
def search():
    query = request.args.get('q', '')
    jobs = Job.query.filter(Job.title.ilike(f'%{query}%')).all()
    return render_template('search.html', jobs=jobs, query=query)

@main.route('/api/search')
def api_search():
    query = request.args.get('q', '')
    jobs = Job.query.filter(Job.title.ilike(f'%{query}%')).all()
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
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        is_employer = request.form.get('is_employer') == 'on'

        user = User.query.filter_by(username=username).first()
        if user:
            flash('Username already exists.', 'error')
        else:
            new_user = User(username=username, is_employer=is_employer)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            flash('Registered successfully. Please log in.', 'success')
            return redirect(url_for('main.login'))

    return render_template('register.html')

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
