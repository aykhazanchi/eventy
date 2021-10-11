from html.entities import html5
from flask import render_template, flash, redirect, request
from flask.helpers import url_for
from flask_login import current_user, login_user
from flask_login.utils import login_required, logout_user
from werkzeug.urls import url_parse
'from our app package import the app instance variable we created'
from app import app, db
from app.forms import LoginForm, RegistrationForm
from app.models import User

'@login_required makes this view a protected view'
@app.route('/')
@app.route('/index')
@login_required
def index():
    user = {}
    posts = [
        {
            'author': {'username': 'CSO'},
            'body': 'Event request created for Telenor'
        },
        {
            'author': {'username': 'SCSO'},
            'body': 'Event request updated for Klarna'
        }
    ]
    return render_template('index.html', title='Home', user=user, posts=posts)


@app.route('/login', methods=['GET', 'POST'])
def login():
    'login a user that is already authenticated'
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = LoginForm()
    'if POST request, run validators to check data'
    if form.validate_on_submit():
        'user has to exist in DB before they can login, we query DB by username provided in form'
        user = User.query.filter_by(username=form.username.data).first()
        'if username doesn\'t exist or password is incorrect, redirect to login page'
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data) ; 'if credentials are correct, store session as login_user and continue to home page'
        next_page = request.args.get('next') ; 'if request comes from login page it has a redirect url already, get that'
        'also check using url_parse whether next_page doesn\'t have a full url to some other domain (could be a malicious attack). in that case go to index instead'
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')    
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('User ' + form.username.data + ' added successfully!')
        return redirect(url_for('index'))
    return render_template('register.html', title='Register User', form=form)

