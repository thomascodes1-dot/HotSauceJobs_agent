from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from flask_login import login_user, login_required, logout_user, current_user
from models import User
from extensions import db
import logging

auth = Blueprint('auth', __name__)

PREDEFINED_USERS = [
    {'username': 'employer1', 'email': 'employer1@example.com', 'password': 'password456', 'role': 'employer'},
    {'username': 'employer2', 'email': 'employer2@example.com', 'password': 'password789', 'role': 'employer'}
]

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = request.form.get('remember') == 'on'

        current_app.logger.info(f"Attempting login for user: {email}")

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user, remember=remember)
            current_app.logger.info(f"Successful login for user: {email}")
            flash('Logged in successfully.', 'success')
            return redirect(url_for('main.index'))
        else:
            current_app.logger.warning(f"Failed login attempt for user: {email}")
            flash('Invalid email or password. Please try again.', 'error')
    
    return render_template('login.html')

@auth.route('/register/<role>', methods=['GET', 'POST'])
def register(role):
    if role not in ['employer', 'job_seeker']:
        flash('Invalid registration type.', 'error')
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email address already exists', 'error')
            return redirect(url_for('auth.register', role=role))

        new_user = User(username=username, email=email, role=role)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful. Please log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template(f'register_{role}.html')

@auth.route('/logout')
@login_required
def logout():
    current_user_email = current_user.email
    logout_user()
    current_app.logger.info(f"User logged out: {current_user_email}")
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))
