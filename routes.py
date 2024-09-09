from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from models import Company, Job, JobApplication
from extensions import db
from werkzeug.utils import secure_filename
import os

main = Blueprint('main', __name__)

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

@main.route('/job/<int:job_id>')
def job_details(job_id):
    job = Job.query.get_or_404(job_id)
    return render_template('job_details.html', job=job)

@main.route('/job/<int:job_id>/apply', methods=['GET', 'POST'])
@login_required
def apply_for_job(job_id):
    job = Job.query.get_or_404(job_id)
    if request.method == 'POST':
        cover_letter = request.form.get('cover_letter')
        resume = request.files.get('resume')
        
        if resume and allowed_file(resume.filename):
            filename = secure_filename(resume.filename)
            resume_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            resume.save(resume_path)
        else:
            flash('Please upload a valid PDF resume.', 'error')
            return redirect(url_for('main.apply_for_job', job_id=job_id))

        application = JobApplication(
            job_id=job.id,
            user_id=current_user.id,
            cover_letter=cover_letter,
            resume=resume_path
        )
        db.session.add(application)
        db.session.commit()

        flash('Your application has been submitted successfully!', 'success')
        return redirect(url_for('main.job_details', job_id=job_id))

    return render_template('apply_for_job.html', job=job)

@main.route('/my_applications')
@login_required
def my_applications():
    applications = JobApplication.query.filter_by(user_id=current_user.id).all()
    return render_template('my_applications.html', applications=applications)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'pdf'
