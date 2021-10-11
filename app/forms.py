from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError
from app.models import User

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign in')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('email', validators=[DataRequired(), Email()])
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

'TODO: RequestForm'