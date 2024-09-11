from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, current_app, abort
from flask_login import login_user, login_required, logout_user, current_user
from models import Company, Job, User, JobApplication
from extensions import db
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from flask_wtf import FlaskForm
from wtforms import TextAreaField, FileField, StringField, SelectField, IntegerField
from wtforms.validators import DataRequired, Optional
import os
import logging

main = Blueprint('main', __name__)

@main.route('/')
def index():
    current_app.logger.info("Accessing the index route")
    companies = Company.query.limit(3).all()
    jobs = Job.query.order_by(Job.id.desc()).limit(5).all()
    return render_template('index.html', companies=companies, jobs=jobs)

@main.route('/api/jobs')
def api_jobs():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    jobs = Job.query.order_by(Job.id.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({
        'jobs': [{
            'id': job.id,
            'title': job.title,
            'company': job.company.name,
            'company_id': job.company_id,
            'description': job.description,
            'job_type': job.job_type,
            'location': job.location,
            'salary_min': job.salary_min,
            'salary_max': job.salary_max
        } for job in jobs.items],
        'has_next': jobs.has_next,
        'total_pages': jobs.pages,
        'current_page': jobs.page
    })

# ... (keep existing code)
