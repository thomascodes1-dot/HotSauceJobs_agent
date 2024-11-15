import os
from flask import Flask, session
from flask_migrate import Migrate
from extensions import db
from models import Company, Job, User, JobApplication
from routes import main
import logging
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
from sqlalchemy.exc import SQLAlchemyError
from flask_login import LoginManager

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'fallback_secret_key')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static/uploads')
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)  # Set session timeout to 30 minutes

    # Configure logging
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]',
                        handlers=[logging.StreamHandler(), logging.FileHandler('app.log')])

    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    db.init_app(app)
    migrate = Migrate(app, db)

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    app.register_blueprint(main)

    # Register error handlers
    app.register_error_handler(404, page_not_found)
    app.register_error_handler(500, internal_server_error)

    # Implement session management
    @app.before_request
    def before_request():
        session.permanent = True
        app.permanent_session_lifetime = timedelta(minutes=30)
        session.modified = True

    # Implement error handling middleware
    @app.errorhandler(Exception)
    def handle_exception(e):
        app.logger.error(f"Unhandled exception: {str(e)}")
        return "An unexpected error occurred", 500

    with app.app_context():
        try:
            db.create_all()
            app.logger.info("Database tables created successfully")
            
            if not User.query.first():
                success = add_sample_data()
                app.logger.info(f"Sample data addition {'succeeded' if success else 'failed'}")
            else:
                app.logger.info("Sample data already exists, skipping addition")
        except SQLAlchemyError as e:
            app.logger.error(f"Error creating database tables: {str(e)}")

    return app

def page_not_found(e):
    return render_template('errors/404.html'), 404

def internal_server_error(e):
    return render_template('errors/500.html'), 500

def add_sample_data():
    try:
        app.logger.info("Adding sample companies and jobs")
        company1 = Company(name="Tech Innovators", description="Leading tech company")
        company2 = Company(name="Green Energy Solutions", description="Sustainable energy provider")
        db.session.add_all([company1, company2])
        db.session.commit()

        job1 = Job(title="Software Engineer", description="Develop cutting-edge software", requirements="5+ years experience in Python", company=company1)
        job2 = Job(title="Data Scientist", description="Analyze complex datasets", requirements="Strong background in statistics and machine learning", company=company1)
        job3 = Job(title="Solar Panel Technician", description="Install and maintain solar panels", requirements="Experience in electrical systems", company=company2)
        db.session.add_all([job1, job2, job3])
        db.session.commit()

        app.logger.info("Adding sample users")
        user1 = User(username="jobseeker1", is_employer=False)
        user1.set_password("password1")
        user2 = User(username="employer1", is_employer=True)
        user2.set_password("password2")
        user3 = User(username="jobseeker2", is_employer=False)
        user3.set_password("password3")
        admin_user = User(username="admin", is_employer=False, is_admin=True)
        admin_user.set_password("adminpassword")
        db.session.add_all([user1, user2, user3, admin_user])
        db.session.commit()

        app.logger.info("Adding sample job applications")
        application1 = JobApplication(job_id=job1.id, user_id=user1.id, status="pending", created_at=datetime.utcnow(), cover_letter="Sample cover letter", resume_filename="sample_resume.pdf")
        application2 = JobApplication(job_id=job2.id, user_id=user3.id, status="accepted", created_at=datetime.utcnow(), cover_letter="Another sample cover letter", resume_filename="another_sample_resume.pdf")
        db.session.add_all([application1, application2])
        db.session.commit()

        companies = Company.query.all()
        jobs = Job.query.all()
        users = User.query.all()
        applications = JobApplication.query.all()
        app.logger.info(f"Verification: {len(companies)} companies, {len(jobs)} jobs, {len(users)} users, {len(applications)} applications")

        print("Sample data added successfully")
        return True
    except SQLAlchemyError as e:
        app.logger.error(f"Error adding sample data: {str(e)}")
        db.session.rollback()
        return False

if __name__ == "__main__":
    app = create_app()
    if os.environ.get('FLASK_ENV') == 'production':
        app.run(host="0.0.0.0", port=5000)
    else:
        app.run(host="0.0.0.0", port=5000, debug=True)
