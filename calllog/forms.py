from flask_wtf import FlaskForm
from flask_mde import Mde, MdeField
from flask_wtf.file import FileField, FileAllowed
from flask_login import current_user
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField, SelectField,DateField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, InputRequired
from calllog.models import User


class LoginForm(FlaskForm):
    email = StringField('Email',validators=[DataRequired(),Email()])
    password = PasswordField('Password',validators=[DataRequired()])
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):

    username = StringField('Username',validators=[DataRequired(),Length(min=2,max=20)])
    email = StringField('Email',validators=[DataRequired(),Email()])
    password = PasswordField('Password',validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password',validators=[DataRequired(),EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_username(self,username):

        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is taken. Please choose a diffrent one.')
            
    def validate_email(self,email):

        user = User.query.filter_by(email=email.data).first()
        check_email_valid = email.data

        if check_email_valid.split('@')[1] != "vxlsoftware.com":

        	raise ValidationError('Please enter your valid vxlsoftware email id.')

        if user:
           raise ValidationError('That email is taken. Please choose a diffrent one.')

class CallLogSummary(FlaskForm):
    title = StringField('Call Agenda',validators=[DataRequired()])
    client_name = StringField('Client Name',validators=[DataRequired()])
    summary = MdeField('Call Summary',validators=[InputRequired("Input Required"),Length(min=50,max=30000)])
    call_attendies = TextAreaField('Call Attendees')
    date_call = DateField('Call Date',format='%d-%m-%Y')
    submit = SubmitField('Post')
    cancel = SubmitField('Cancel')