from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db, login

class User(UserMixin, db.Model):
    'db.Model is a base class for all models from SQLAlchemy'
    id = db.Column(db.Integer, primary_key=True) ; 'set as primary key'
    username = db.Column(db.String(64), index=True)
    email = db.Column(db.String(120), index=True)
    password_hash = db.Column(db.String(120)) ; 'store a hashed password instead of cleartext'
    name = db.Column(db.String(64))
    role = db.Column(db.String(8)) 
    # Roles can only be of type: cso, scso, fm, am, hr, sm (SM manager), pm (PM manager), epm (Event Planning manager), smtm (SM team member), pmtm (PM team member)

    def set_role(self, role):
        self.role = role
    
    '''define a one-to-many relationship between users and requests
    The backref argument defines the name of a field that will be added 
    to the objects of the "many" class that points back at the "one" object. 
    This will add a request.creator expression that will return the user given a request. 
    '''
    requests = db.relationship('Request', backref='creator', lazy='dynamic')

    'set password as hash'
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    'check password to see if it matches'
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return '<User {}>'.format(self.username)


class Request(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_name = db.Column(db.String(64), index=True)
    event_type = db.Column(db.String(64), index=True)
    event_details = db.Column(db.String(120))
    client_budget = db.Column(db.Integer)
    feedback = db.Column(db.String(120))
    created_by = db.Column(db.String(64)) # not really changed, more a view for CSO and SCSO
    assigned_to = db.Column(db.String(64)) # maps to username or sub team
    status = db.Column(db.String(64))
    #event_date = db.Column(db.Date())
    ready_for_planning = db.Column(db.Boolean(False))
    tasks_for = db.Column(db.String(64))
    
    tasks = db.relationship('Task', backref='event', lazy='dynamic')

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def set_assigned_to(self, assigned_to):
        self.assigned_to = assigned_to    

    def __repr__(self):
        return '<Request {}>'.format(self.body)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_name = db.Column(db.String(64), index=True)
    task_details = db.Column(db.String(120), index=True)
    created_by = db.Column(db.String(64)) # Always SM or PM
    subteam = db.Column(db.String(64))

    request = db.Column(db.Integer, db.ForeignKey('request.id'))

    def __repr__(self):
        return '<Task {}>'.format(self.body)

'define a user loader function for user login and logged-in sessions'
@login.user_loader
def load_user(id):
    return User.query.get(int(id))