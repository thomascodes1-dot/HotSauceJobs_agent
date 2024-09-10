import os
from flask import Flask
from extensions import db
from flask_login import LoginManager
import logging
from datetime import datetime

def create_app():
    app = Flask(__name__)
    database_url = os.environ.get("DATABASE_URL")
    if database_url and database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "your-secret-key")
    
    # Configure upload folder
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'uploads')
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    
    db.init_app(app)

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'

    @login_manager.user_loader
    def load_user(user_id):
        from models import User
        return User.query.get(int(user_id))

    with app.app_context():
        from routes import main
        app.register_blueprint(main)
        
        import models
        db.create_all()  # Create tables if they don't exist
        
        if not models.Company.query.first():  # Only add sample data if the database is empty
            success = add_sample_data()
            logging.info(f"Sample data addition {'succeeded' if success else 'failed'}")

    return app

def add_sample_data():
    from models import Company, Job, User, JobApplication
    from sqlalchemy.exc import SQLAlchemyError

    try:
        # Add sample companies
        logging.info("Adding sample companies and jobs")
        company1 = Company(name="Tech Innovators", description="Leading tech company")
        company2 = Company(name="Green Energy Solutions", description="Sustainable energy provider")
        db.session.add_all([company1, company2])
        db.session.commit()

        # Add sample jobs
        job1 = Job(title="Software Engineer", description="Develop cutting-edge software", requirements="5+ years experience in Python", company=company1)
        job2 = Job(title="Data Scientist", description="Analyze complex datasets", requirements="Strong background in statistics and machine learning", company=company1)
        job3 = Job(title="Solar Panel Technician", description="Install and maintain solar panels", requirements="Experience in electrical systems", company=company2)
        db.session.add_all([job1, job2, job3])
        db.session.commit()

        # Add sample users
        logging.info("Adding sample users")
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

        # Add sample job applications
        logging.info("Adding sample job applications")
        application1 = JobApplication(job_id=job1.id, user_id=user1.id, status="pending", created_at=datetime.utcnow(), cover_letter="Sample cover letter", resume_filename="sample_resume.pdf")
        application2 = JobApplication(job_id=job2.id, user_id=user3.id, status="accepted", created_at=datetime.utcnow(), cover_letter="Another sample cover letter", resume_filename="another_sample_resume.pdf")
        db.session.add_all([application1, application2])
        db.session.commit()

        print("Sample data added successfully")
        return True
    except SQLAlchemyError as e:
        logging.error(f"Error adding sample data: {str(e)}")
        db.session.rollback()
        return False

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
