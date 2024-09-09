from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, login_required, logout_user
from models import User
from extensions import db
import logging

auth = Blueprint('auth', __name__)

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        is_employer = request.form.get('is_employer') == 'on'

        current_app.logger.info(f"Attempting to register user with email: {email}")

        # Check if user already exists
        existing_user = User.query.filter((User.email == email) | (User.username == username)).first()
        if existing_user:
            if existing_user.email == email:
                flash('Email address already exists', 'error')
                current_app.logger.warning(f"Registration failed: Email {email} already exists")
            else:
                flash('Username already exists', 'error')
                current_app.logger.warning(f"Registration failed: Username {username} already exists")
            return redirect(url_for('auth.register'))

        new_user = User(username=username, email=email, is_employer=is_employer)
        new_user.set_password(password)

        try:
            db.session.add(new_user)
            db.session.commit()
            current_app.logger.info(f"Successfully registered user: {email}")
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error during registration for {email}: {str(e)}")
            flash('An error occurred during registration. Please try again.', 'error')
            return redirect(url_for('auth.register'))

    return render_template('register.html')

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = request.form.get('remember') == 'on'

        current_app.logger.info(f"Attempting login for user: {email}")

        try:
            user = User.query.filter_by(email=email).first()
            if user and user.check_password(password):
                login_user(user, remember=remember)
                current_app.logger.info(f"Successful login for user: {email}")
                flash('Logged in successfully.', 'success')
                next_page = request.args.get('next')
                return redirect(next_page or url_for('main.index'))
            else:
                current_app.logger.warning(f"Failed login attempt for user: {email}")
                flash('Invalid email or password. Please try again.', 'error')
        except Exception as e:
            current_app.logger.error(f"Error during login for {email}: {str(e)}")
            flash('An error occurred during login. Please try again.', 'error')

    return render_template('login.html')

@auth.route('/logout')
@login_required
def logout():
    current_user_email = current_user.email
    logout_user()
    current_app.logger.info(f"User logged out: {current_user_email}")
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))
