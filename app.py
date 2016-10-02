import os

from flask import Flask, g, render_template, redirect, url_for
from flask_login import LoginManager, login_required, current_user
from flaskext.markdown import Markdown

from posts import posts_blueprint
from accounts import accounts_blueprint
from users import users_blueprint
from comments import comments_blueprint
from notifications import notifications_blueprint
from search import search_blueprint

import models

app = Flask(__name__)
app.secret_key = 'rw8efuhjeqr38efygduvbefjkqgiuwohv3k2r112qwfay98qughgiuwr23tw89ry0f'

app.register_blueprint(posts_blueprint)
app.register_blueprint(accounts_blueprint)
app.register_blueprint(users_blueprint)
app.register_blueprint(comments_blueprint)
app.register_blueprint(notifications_blueprint)
app.register_blueprint(search_blueprint)

RECAPTCHA_PUBLIC_KEY = os.environ['SOSHIL_RECAPTCHA_PUBLIC_KEY']
RECAPTCHA_PRIVATE_KEY = os.environ['SOSHIL_RECAPTCHA_PRIVATE_KEY']
app.config.from_object(__name__)

markdown = Markdown(app)

DEBUG = True
PORT = int(os.environ.get('PORT', 8000))
HOST = '0.0.0.0'

@app.context_processor
def inject_user():
    return dict(user=g.user._get_current_object())

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.session_protection = 'strong'
login_manager.login_view = 'accounts.log_in'

@login_manager.user_loader
def load_user(userid):
    try:
        return models.User.get(models.User.id == userid)
    except models.DoesNotExist:
        return None

@app.before_request
def before_request():
    """Connect to the database before each request."""
    g.db = models.db_proxy
    g.db.connect()
    g.user = current_user

@app.after_request
def after_request(response):
    '''Close the database connection after each request'''
    g.db.close()
    return response

@app.errorhandler(404)
def page_not_found(error):
    return render_template('error.html', num=404), 404

@app.errorhandler(401)
def unauthorized(error):
    return render_template('error.html', num=401), 401

@app.errorhandler(403)
def forbidden(error):
    return render_template('error.html', num=403), 403

@app.errorhandler(500)
def internal_server_error(error):
    return render_template('error.html', num=500), 500

@app.route('/')
def index():
    if g.user._get_current_object().is_authenticated:
        return redirect(url_for('posts.stream'))
    else:
        return render_template('index.html')

@app.route('/welcome')
@login_required
def welcome():
    return render_template('welcome.html')

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/google46cfa7a8f3f231ed.html')
def google_verify():
    return 'google-site-verification: google46cfa7a8f3f231ed.html'

if __name__ == '__main__':
    models.initialize()

    try:
        models.User.create_user(
            username='Hum4n01d',
            email='hum4n01d@icloud.com',
            password='',
            avatar_url='https://avatars.githubusercontent.com/u/17228477?v=3',
            github_user=True,
            admin=True
        )
    except ValueError:
        pass

    production = not os.environ.get('DEBUG', True)

    if production:
        app.run(host=HOST, port=PORT)

    else:
        extra_dirs = ['templates/']
        extra_files = extra_dirs[:]
        for extra_dir in extra_dirs:
            for dirname, dirs, files in os.walk(extra_dir):
                for filename in files:
                    filename = os.path.join(dirname, filename)
                    if os.path.isfile(filename):
                        extra_files.append(filename)

        app.run(debug=True, port=int(os.environ.get('PORT', 5000)), host=HOST,
                extra_files=extra_files)