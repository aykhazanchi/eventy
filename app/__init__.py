from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_bootstrap import Bootstrap

'''
create application object as an instance of class Flask
__name__ is a predefined python variable set to the name of the module
Flask uses location of where module is located as a starting point for other resources

this app is an instance variable, not related to app package which is the directory
'''
app = Flask(__name__)

'from "config" module read configuration from "Config" class'
app.config.from_object(Config)

'setup db'
db = SQLAlchemy(app)
migrate = Migrate(app, db)

'setup login plugin'
login = LoginManager(app)
'''
define which function is for login and force login on protected views
protect views by using @login_required as a decorator on their functions
'''
login.login_view = 'login'

'setup bootstrap'
bootstrap = Bootstrap(app)

'''
import the routes module from our 'app' package which is the name of our directory
this 'app' is a reference to the module, which is the same as the name of the directory
where __init.py__ is located. this is saying import 'routes' function from 'app' module

Another peculiarity is that the routes module is imported at the bottom 
and not at the top of the script as it is always done. The bottom import 
is a workaround to circular imports, a common problem with Flask 
applications. You are going to see that the routes module needs to import 
the app variable defined in this script, so putting one of the reciprocal 
imports at the bottom avoids the error that results from the mutual 
references between these two files.
'''
from app import routes, models
