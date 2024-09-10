from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_user, login_required, logout_user, current_user
from models import Company, Job, User
from extensions import db
from werkzeug.security import check_password_hash, generate_password_hash
import logging

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

@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        logging.info(f"Login attempt for username: {username}")
        user = User.query.filter_by(username=username).first()
        if user:
            logging.info(f"User found: {user.username}")
            if check_password_hash(user.password_hash, password):
                login_user(user)
                logging.info(f"User {username} logged in successfully")
                flash('Logged in successfully.', 'success')
                return redirect(url_for('main.index'))
            else:
                logging.warning(f"Invalid password for user: {username}")
        else:
            logging.warning(f"User not found: {username}")
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
