from flask import render_template, flash, redirect, request, session
from flask.helpers import url_for
from flask_login import current_user, login_user
from flask_login.utils import login_required, logout_user
from flask_migrate import current
from werkzeug.urls import url_parse
from wtforms.fields.core import StringField
'from our app package import the app instance variable we created'
from app import app, db
from app.forms import LoginForm, RegistrationForm, RequestForm, TaskForm
from app.models import Task, User, Request, load_user

'@login_required makes this view a protected view'
@app.route('/')
@app.route('/index')
@app.route('/home')
@login_required
def index():
    # for each user, show their assigned and created requests
    user = current_user.username
    role = current_user.role
    assigned_requests = Request.query.filter_by(assigned_to=role).order_by(Request.id.desc())
    updated_requests = Request.query.filter_by(created_by=user).order_by(Request.id.desc())
    return render_template('index.html', title='Home', user=user, assigned_requests=assigned_requests, updated_requests=updated_requests)


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
        login_user(user, remember=form.remember_me.data) 
        'if credentials are correct, store session as login_user and continue to home page'
        next_page = request.args.get('next') 
        'if request comes from login page it has a redirect url already, get that'
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
        user = User(name=form.name.data, username=form.username.data, 
            email=form.email.data, role=form.role.data)
        user.set_password(form.password.data)

        db.session.add(user)
        db.session.commit()
        flash('User ' + form.username.data + ' added successfully!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register User', form=form)

@app.route('/new-request', methods=['GET', 'POST'])
@login_required
def new_request():
    if current_user.role is None:
        return redirect(url_for('login'))
    if current_user.role != 'cso' and current_user.role != 'scso': # redirect for everyone except cso and scso
        return redirect(url_for('index'))
    'if users are cso or scso then we show the request form'
    form = RequestForm()
    if form.validate_on_submit():
        req = Request(client_name=form.client_name.data, 
            event_type=form.event_type.data, event_details=form.event_details.data,
            client_budget=form.client_budget.data, feedback=form.feedback.data, status=form.status.data, created_by=current_user.username)

        set_assigned_to(req, None)
        
        db.session.add(req)
        db.session.commit()

        flash('Request for client ' + form.client_name.data + ' created successfully!')
        return redirect(url_for('index'))
    return render_template('request.html', title='Create New Request', form=form)

@app.route('/pending-updates', methods=['GET'])
@login_required
def pending_updates():
    if current_user.role is None:
        return redirect(url_for('login'))
    if current_user.role == 'cso':
        return redirect(url_for('index'))
    # get all pending requests assigned to this role/user
    reqs = Request.query.filter_by(assigned_to=current_user.role).all()
    return render_template('pending-updates.html', title='Update Pending Requests', reqs=reqs)

@app.route('/update-request/<reqid>', methods=['GET', 'POST'])
@login_required
def update_request(reqid):
    if current_user.role is None:
        return redirect(url_for('login'))
    if current_user.role == 'cso':
        return redirect(url_for('index'))
    # pull the url
    req = Request.query.filter_by(id=reqid).first_or_404()
    form = RequestForm()

    # when POST call, means request is updated
    if form.validate_on_submit():
        if form.closesubmit.data:
            req.status = 'Rejected'
            set_assigned_to(req, 'scso')
            db.session.add(req)
            db.session.commit()
            flash('Request status updated')
            return redirect(url_for('index'))
        # save the edits
        # When GET call, show the request based on specific request ID
        req.client_name=form.client_name.data
        req.event_type=form.event_type.data
        req.event_details=form.event_details.data
        req.client_budget=form.client_budget.data
        req.feedback=form.feedback.data
        req.created_by=current_user.username
        req.status=form.status.data
        set_assigned_to(req, None)
        # set ready_for_planning=true if approval is by AM
        if current_user.role == 'am':
            req.ready_for_planning = True
        # set ready_for_tasks=true if planning = True and approval is by SCSO
        if current_user.role == 'scso' and req.ready_for_planning is True:
            if form.servicessubmit.data:
                req.tasks_for = 'services'
                set_assigned_to(req, 'sm')
            elif form.productionsubmit.data:
                req.tasks_for = 'production'
                set_assigned_to(req, 'pm')
        db.session.commit()
        flash('Request details updated for ' + form.client_name.data)
        return redirect(url_for('index'))

    elif request.method == 'GET':
        form.client_name.data = req.client_name
        form.event_type.data = req.event_type
        form.event_details.data = req.event_details
        form.client_budget.data = req.client_budget
        form.status.data = req.status
        
    return render_template('update.html', title='Update Request', req=req, form=form)

def set_assigned_to(req, role):
    if not role is None:
        req.set_assigned_to(role)
    elif current_user.role == 'cso':
        req.set_assigned_to('scso')
    elif current_user.role == 'scso':
        req.set_assigned_to('fm')
    elif current_user.role == 'fm':
        req.set_assigned_to('am')
    elif current_user.role == 'am':
        req.set_assigned_to('scso')

# show all request tickets ready for planning
@app.route('/planning', methods=['GET', 'POST'])
@login_required
def planning_dashboard():
    if current_user.role == 'sm':
        reqs = Request.query.filter_by(tasks_for='services').all()
    elif current_user.role == 'pm':
        reqs = Request.query.filter_by(tasks_for='production').all()
    elif current_user.role is None:
        return redirect(url_for('login'))
    else:
        return redirect(url_for('index'))
    
    return render_template('planning.html', title='Planning Dashboard', reqs=reqs)

# allow adding tasks to a specific ticket
@app.route('/request/<reqid>/tasks', methods=['GET', 'POST'])
@login_required
def add_tasks(reqid):
    if current_user.role is None:
        return redirect(url_for('login'))
    if current_user.role != 'sm' and current_user.role != 'pm':
        return redirect(url_for('index'))
    
    form = TaskForm()
    req = Request.query.filter_by(id=reqid).first()
    
    form.linked_to.data = req.id

    if form.validate_on_submit():
        task = Task(task_name=form.task_name.data, task_details=form.task_details.data, 
            subteam=form.subteam.data, owner=form.owner.data)
        task.created_by = current_user.role
        
        db.session.add(task)
        db.session.commit()
        flash('Task ' + form.task_name.data + ' successfully added!')
        return redirect(url_for('view_tasks'))
    return render_template('add-tasks.html', title='Add Tasks', req=req, form=form)


# view list of all tasks for all tickets
@app.route('/all-tasks', methods=['GET'])
@login_required
def view_tasks():
    if current_user.role is None:
        return redirect(url_for('login'))
    if current_user.role != 'sm' and current_user.role != 'pm' and current_user.role != 'smtm' and current_user.role != 'pmtm':
        return redirect(url_for('index'))
    
    # get all tasks
    tasks = Task.query.filter_by().order_by(Task.request.desc())
    return render_template('tasks.html', title='Task Dashboard', tasks=tasks)
