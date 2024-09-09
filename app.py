import os
from flask import Flask
from extensions import db

def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
    db.init_app(app)

    with app.app_context():
        from routes import main
        app.register_blueprint(main)
        
        import models
        db.create_all()
        
        add_sample_data()

    return app

def add_sample_data():
    from models import Company, Job

    # Check if data already exists
    if Company.query.first() is None:
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

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
