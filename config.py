import os

'find its own directory as absolute path and set that as the baseDir'
baseDir = os.path.abspath(os.path.dirname(__file__))

'''
The SECRET_KEY configuration variable that I added as the only configuration 
item is an important part in most Flask applications. Flask and some of its 
extensions use the value of the secret key as a cryptographic key, 
useful to generate signatures or tokens.
'''
class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'this-is-a-default-secret'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(baseDir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False