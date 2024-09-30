from extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class Company(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    image = db.Column(db.String(255), nullable=True)
    cover_photo = db.Column(db.String(255), nullable=True)
    jobs = db.relationship('Job', backref='company', lazy=True)

class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    requirements = db.Column(db.Text, nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    applications = db.relationship('JobApplication', backref='job', lazy=True)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_employer = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default=False)
    applications = db.relationship('JobApplication', backref='applicant', lazy=True)
    company_name = db.Column(db.String(100), nullable=True)
    company_description = db.Column(db.Text, nullable=True)
    profile_picture = db.Column(db.String(255), nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class JobApplication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    cover_letter = db.Column(db.Text, nullable=False)
    resume_filename = db.Column(db.String(255), nullable=False)
