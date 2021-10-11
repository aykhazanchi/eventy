'from the app package import the app instance variable'
from app import app, db
from app.models import User, Post

'useful for debugging, define shell constants when using `flask shell` for debug'
@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Post': Post}
