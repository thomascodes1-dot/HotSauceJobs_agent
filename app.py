import os
from flask import Flask
from flask_login import LoginManager
from extensions import db
import logging
from sqlalchemy.exc import SQLAlchemyError

def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL") + "?sslmode=require"
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "fallback_secret_key")
    
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    app.logger.setLevel(logging.INFO)

    # Initialize database
    try:
        db.init_app(app)
        app.logger.info("Database initialized successfully")
    except SQLAlchemyError as e:
        app.logger.error(f"Error initializing database: {str(e)}")
        raise

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    @login_manager.user_loader
    def load_user(user_id):
        from models import User
        return User.query.get(int(user_id))

    with app.app_context():
        from routes import main
        app.register_blueprint(main)

        from auth import auth as auth_blueprint
        app.register_blueprint(auth_blueprint)
        
        import models
        try:
            db.create_all()
            app.logger.info("Database tables created successfully")
        except SQLAlchemyError as e:
            app.logger.error(f"Error creating database tables: {str(e)}")
            raise
        
        add_sample_data()

    return app

def add_sample_data():
    from models import Company, Job

    # Check if data already exists
    if Company.query.first() is None:
        try:
            # Add sample companies
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
            
            current_app.logger.info("Sample data added successfully")
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Error adding sample data: {str(e)}")

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
