from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, FileField, BooleanField, PasswordField
from wtforms.validators import DataRequired, Length, Optional
from flask_wtf.file import FileAllowed, FileField

class CompanyForm(FlaskForm):
    name = StringField('Company Name', validators=[DataRequired()])
    description = TextAreaField('Company Description', validators=[DataRequired()])
    image = FileField('Company Image', validators=[FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')])
    submit = SubmitField('Submit')

class JobForm(FlaskForm):
    title = StringField('Job Title', validators=[DataRequired()])
    description = TextAreaField('Job Description', validators=[DataRequired()])
    requirements = TextAreaField('Job Requirements', validators=[DataRequired()])
    submit = SubmitField('Submit')

class JobApplicationForm(FlaskForm):
    cover_letter = TextAreaField('Cover Letter', validators=[DataRequired()])
    resume = FileField('Resume', validators=[DataRequired(), FileAllowed(['pdf'], 'PDF files only!')])
    submit = SubmitField('Submit Application')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    password = PasswordField('Password', validators=[DataRequired()])
    is_employer = BooleanField('Register as an employer')
    company_name = StringField('Company Name', validators=[Optional(), Length(max=100)])
    company_description = TextAreaField('Company Description', validators=[Optional()])
    profile_picture = FileField('Profile Picture', validators=[FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')])
    submit = SubmitField('Sign Up')
