from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, FileField
from wtforms.validators import DataRequired
from flask_wtf.file import FileAllowed

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
