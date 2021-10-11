from datetime import datetime
from enum import unique
from operator import index
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db, login

class User(UserMixin, db.Model):
    'db.Model is a base class for all models from SQLAlchemy'
    id = db.Column(db.Integer, primary_key=True) ; 'set as primary key'
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(120)) ; 'store a hashed password instead of cleartext'

    '''define a one-to-many relationship between users and posts
    The backref argument defines the name of a field that will be added 
    to the objects of the "many" class that points back at the "one" object. 
    This will add a post.author expression that will return the user given a post. 
    '''
    db.relationship('Post', backref='author', lazy='dynamic')

    'set password as hash'
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    'check password to see if it matches'
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    'repr just tells python how to print objects of this class, for debugging'
    def __repr__(self):
        return '<User {}>'.format(self.username)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    'reference the user id to link posts to a user id'
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<Post {}>'.format(self.body)

'''
The user_id field was initialized as a foreign key to user.id, which means that it references an 
id value from the users table. In this reference the user part is the name of the database table 
for the model. It is an unfortunate inconsistency that in some instances such as in a db.relationship() 
call, the model is referenced by the model class, which typically starts with an uppercase character, 
while in other cases such as this db.ForeignKey() declaration, a model is given by its database table 
name, for which SQLAlchemy automatically uses lowercase characters and, for multi-word model names, snake case.
'''

'define a user loader function for user login'
@login.user_loader
def load_user(id):
    return User.query.get(int(id))