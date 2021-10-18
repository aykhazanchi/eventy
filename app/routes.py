from flask import render_template, flash, redirect, request, session
from flask.helpers import url_for
from flask_login import current_user, login_user
from flask_login.utils import login_required, logout_user
from flask_migrate import current
from werkzeug.urls import url_parse
from wtforms.fields.core import StringField
'from our app package import the app instance variable we created'
from app import app, db
from app.forms import BudgetForm, LoginForm, RegistrationForm, RequestForm, ResourceForm, TaskForm
from app.models import Budget, Resource, Task, User, Request, load_user

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
    subteam = current_user.role + 'tm'
    form.subteam.data = subteam

    if form.validate_on_submit():
        task = Task(task_name=form.task_name.data, task_details=form.task_details.data, 
            subteam=subteam)
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
    
    if current_user.role == 'smtm' or current_user.role == 'pmtm':
        subteam = current_user.role
    else:
        subteam = current_user.role + 'tm'
    # get all tasks by subteam
    tasks = Task.query.filter_by(subteam=subteam).order_by(Task.request.desc())
    return render_template('tasks.html', title='Task Dashboard', tasks=tasks)

@app.route('/new-resource', methods=['GET', 'POST'])
@login_required
def new_resource():
    if current_user.role is None:
        return redirect(url_for('login'))
    if current_user.role != 'sm' and current_user.role != 'pm':
        return redirect(url_for('index'))
    
    form = ResourceForm()

    if form.validate_on_submit():
        res = Resource(job_title=form.job_title.data, job_profile=form.job_profile.data,
            experience_reqd=form.experience_reqd.data, salary_max=form.salary_max.data,
            salary_min=form.salary_min.data)
        res.created_by = current_user.role
        res.assigned_to = 'hr'

        db.session.add(res)
        db.session.commit()
        
        flash('Resource request raised successfully!')
        return redirect(url_for('index'))

    return render_template('resource.html', title='Resource Request Form', form=form)

@app.route('/all-resources', methods=['GET'])
@login_required
def all_resources():
    if current_user.role is None:
        return redirect(url_for('login'))
    if current_user.role != 'hr':
        return redirect(url_for('index'))
    
    # get all resource requests
    resources = Resource.query.filter_by(assigned_to=current_user.role)
    return render_template('all-resources.html', title='Resource Requests', resources=resources)

@app.route('/update-resource/<resid>', methods=['GET', 'POST'])
@login_required
def update_resource(resid):
    if current_user.role is None:
        return redirect(url_for('login'))
    if current_user.role != 'hr':
        return redirect(url_for('index'))

    res = Resource.query.filter_by(id=resid).first_or_404()
    form = ResourceForm()

    if form.validate_on_submit():
        res.job_title = form.job_title.data
        res.job_profile = form.job_profile.data
        res.experience_reqd = form.experience_reqd.data
        res.salary_max = form.salary_max.data
        res.salary_min = form.salary_min.data
        if current_user.role == 'hr':
            if res.created_by == 'sm':
                res.assigned_to = 'sm'
            elif res.created_by == 'pm':
                res.assigned_to = 'pm'
            else:
                res.assigned_to = 'hr'
        elif current_user.role == 'sm' or current_user.role == 'pm':
            res.assigned_to = 'hr'
        db.session.add(res)
        db.session.commit(res)
        flash('Resource request updated successfully!')
        return redirect(url_for('index'))
    elif request.method == 'GET':
        form.job_title.data = res.job_title
        form.job_profile.data = res.job_profile
        form.experience_reqd.data = res.experience_reqd
        form.salary_max.data = res.salary_max
        form.salary_min.data = res.salary_min
        
    return render_template('resource.html', title='Update Resource Request', res=res, form=form)

@app.route('/new-budget', methods=['GET', 'POST'])
@login_required
def new_budget():
    if current_user.role is None:
        return redirect(url_for('login'))
    if current_user.role != 'sm' and current_user.role != 'pm':
        return redirect(url_for('index'))
    
    form = BudgetForm()

    if form.validate_on_submit():
        budget = Budget(budget_for=form.budget_for.data, budget_quote=form.budget_quote.data,
            budget_details=form.budget_details.data)
        budget.created_by = current_user.role
        budget.assigned_to = 'fm'

        db.session.add(budget)
        db.session.commit()
        
        flash('Budget request raised successfully!')
        return redirect(url_for('index'))

    return render_template('budget.html', title='Budget Request Form', form=form)

@app.route('/all-budgets', methods=['GET'])
@login_required
def all_budgets():
    if current_user.role is None:
        return redirect(url_for('login'))
    if current_user.role != 'pm':
        return redirect(url_for('index'))
    
    # get all budget requests
    budgets = Budget.query.filter_by(assigned_to=current_user.role)
    return render_template('all-budgets.html', title='Budget Requests', budgets=budgets)

@app.route('/update-budget/<budgetid>', methods=['GET', 'POST'])
@login_required
def update_budget(budgetid):
    if current_user.role is None:
        return redirect(url_for('login'))
    if current_user.role != 'fm':
        return redirect(url_for('index'))

    budget = Budget.query.filter_by(id=budgetid).first_or_404()
    form = BudgetForm()

    if form.validate_on_submit():
        budget.budget_for = form.budget_for.data
        budget.budget_quote = form.budget_quote.data
        budget.budget_details = form.budget_details.data
        if current_user.role == 'hr':
            if budget.created_by == 'sm':
                budget.assigned_to = 'sm'
            elif budget.created_by == 'pm':
                budget.assigned_to = 'pm'
            else:
                budget.assigned_to = 'hr'
        elif current_user.role == 'sm' or current_user.role == 'pm':
            budget.assigned_to = 'hr'
        db.session.add(budget)
        db.session.commit(budget)
        flash('Budget request updated successfully!')
        return redirect(url_for('index'))
    elif request.method == 'GET':
        form.budget_for.data = budget.budget_for
        form.budget_quote.data = budget.budget_quote
        form.budget_details.data = budget.budget_details
        
    return render_template('budget.html', title='Update Budget Request', budget=budget, form=form)
