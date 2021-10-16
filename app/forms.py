from typing import Text
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, RadioField
from wtforms.fields.core import DateField, IntegerField, Label
from wtforms.fields.simple import TextAreaField, TextField
from wtforms.validators import DataRequired, Email, EqualTo, NumberRange, ValidationError
from wtforms.widgets.core import TextArea
from app.models import User

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign in')

class RegistrationForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    role = RadioField('Role', choices=[('cso', 'Customer Service Officer'), 
        ('scso', 'Senior Customer Service Officer'), ('am', 'Administrative Manager'),
        ('fm', 'Financial Manager'), ('sm', 'Services Manager'), 
        ('pm', 'Production Manager'), ('hr', 'Human Resources Manager'), 
        ('smtm', 'Services Team Member'), ('pmtm', 'Production Team Member')])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', 
        validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        'Check username doesn\'t already exist in DB'
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Username already exists. Please use a different username.')

    def validate_email(self, email):
        'Check email doesn\'t already exist in DB'
        email = User.query.filter_by(email=email.data).first()
        if email is not None:
            raise ValidationError('Email already exists. Please use a different email.')

'TODO: Check if these fields make sense?'

class RequestForm(FlaskForm):
    client_name = StringField('Client Name', validators=[DataRequired()])
    event_type = StringField('Event Type', validators=[DataRequired()])
    event_details = TextField('Event Details', validators=[DataRequired()])
    client_budget = IntegerField('Budget', validators=[DataRequired(), NumberRange(min=1000)])
    submit = SubmitField('Submit')
    servicessubmit = SubmitField('Send to Services Team')
    productionsubmit = SubmitField('Send to Production Team')


class TaskForm(FlaskForm):
    task_name = StringField('Task Name', validators=[DataRequired()])
    task_details = TextAreaField('Task Details', validators=[DataRequired()])
    subteam = RadioField('Assign to Sub Team', choices=[('services', 'Services Management'),
        ('production', 'Production Management')])
    owner = StringField('Owner', default=None)
    linked_to = TextField('Linked Request ID:')
    submit = SubmitField('Submit')