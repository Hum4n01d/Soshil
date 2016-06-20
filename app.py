import os

import requests
from flask import Flask, g, render_template, flash, redirect, url_for, request
from flask_bcrypt import check_password_hash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_sslify import SSLify

app = Flask(__name__)
sslify = SSLify(app)
app.secret_key = 'rw8efuhjeqr38efygduvbefjkqgiuwohv3k2r112qwfay98qughgiuwr23tw89ry0f'

import forms
import models

DEBUG = True
PORT = 8000
HOST = '0.0.0.0'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.session_protection = 'strong'
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(userid):
    try:
        return models.User.get(models.User.id == userid)
    except models.DoesNotExist:
        return None

@app.before_request
def before_request():
    '''Connect to the database before each request'''
    g.db = models.db_proxy
    g.db.connect()
    g.user = current_user

@app.after_request
def after_request(response):
    '''Close the database connection after each request'''
    g.db.close()
    return response

@app.route('/register', methods=('GET', 'POST'))
def register():
    form = forms.RegisterForm()
    if form.validate_on_submit():
        flash('You\'ve been successfully registered!', 'success')
        models.User.create_user(
            username=form.username.data,
            low_username=form.username.data.lower(),
            email=form.email.data.lower(),
            password=form.password.data
        )
        login_user(models.User.get(models.User.email == form.email.data))
        return redirect(url_for('index'))
    
    return render_template('register.html', form=form, user=g.user)

@app.route('/login', methods=('GET', 'POST'))
def login():
    form = forms.LoginForm()
    next_url = request.args.get('next')
    
    if form.validate_on_submit():
        try:
            user = models.User.get(models.User.low_username == form.username.data.lower())
            
        except models.DoesNotExist:
            flash('Your username or password is incorrect', 'error')
        else:
            if user.github_user:
                flash('Please sign in through Github', 'error')
            else:
                if check_password_hash(user.password, form.password.data):
                    login_user(user)
                    flash('You are now logged in {}'.format(user.username), 'success')
                    
                    if next_url:
                        return redirect(next_url)
                    
                    else:
                        return redirect(url_for('index'))

                else:
                    flash('Your email or password is incorrect', 'error')
                
    return render_template('login.html', form=form, user=g.user)

@app.route('/login/github')
def login_github():
    CLIENT_ID = os.environ['CLIENT_ID']
    return redirect('https://github.com/login/oauth/authorize?scope=user:email&client_id=' + CLIENT_ID)

@app.route('/login/github/callback')
def login_github_callback():
    code = request.args.get('code')
    response = requests.post('https://github.com/login/oauth/access_token', {
        "client_id": os.environ['CLIENT_ID'],
        "client_secret": os.environ['CLIENT_SECRET'],
        "code": code
    }, headers={"accept": "application/json"})
    
    access_token = response.json()['access_token']
    
    username = requests.get('https://api.github.com/user', {"access_token": access_token}).json()['login']
    emails = requests.get('https://api.github.com/user/emails', {"access_token": access_token}).json()
    email = ''
    
    for address in emails:
        if address['primary']:
            if address['verified']:
                    email = address['email']        
            else:
                flash('Please verify your Github account', 'error')
    
    try:
        models.User.create_user(
            username=username,
            low_username=username.lower(),
            email=email.lower(),
            password='',
            github_user=True
        )
    except: pass
    
    user = models.User.get(models.User.email == email)
            
    login_user(user)
    flash("You've been logged in!", "success")
    
    return redirect(url_for('index'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You\'ve been logged out.', 'success')
    return redirect(url_for('login'))

@app.route('/')
def index():
    stream = models.Post.select().limit(100)
    
    return render_template('stream.html', user=g.user._get_current_object, stream=stream)

@app.route('/stream')
@app.route('/stream/<username>')
def stream(username=None):
    template = 'stream.html'
    profile_user = None
    stream = None

    if username:
        template = 'profile.html'

        try:
            if g.user._get_current_object().is_anonymous:
                profile_user = models.User.select().where(models.User.username ** username).get()
                stream = profile_user.posts.limit(100)

            elif username != current_user.username:
                profile_user = models.User.select().where(models.User.username ** username).get()
                stream = profile_user.posts.limit(100)

            else:
                stream = current_user.get_stream().limit(100)
                profile_user = current_user

        except models.DoesNotExist:
            return render_template('error.html', error=(404, 'User not found'), user=g.user)
    else:
        stream = current_user.get_stream().limit(100)
        profile_user = current_user

    return render_template(template, profile_user=profile_user, stream=stream, user=g.user._get_current_object())

@app.route('/new_post', methods=('GET', 'POST'))
@login_required
def post():
    form = forms.PostForm()
    if form.validate_on_submit():
        models.Post.create(user=g.user._get_current_object(), title=form.title.data, content=form.content.data.strip())
        flash('Message successfully posted!', 'success')
        return redirect(url_for('index'))
    
    return render_template('post.html', form=form, user=g.user)


@app.route('/follow/<username>')
@login_required
def follow(username):
    try:
        to_user = models.User.get(models.User.username ** username)
    except models.DoesNotExist:
        pass
    else:
        try:
            models.Relationship.create(
                from_user=g.user._get_current_object(),
                to_user=to_user
            )
        except models.IntegrityError:
            pass
        else:
            flash("You're now following {}".format(to_user.username), 'success')

    return redirect(url_for('stream', username=to_user.username))


@app.route('/unfollow/<username>')
@login_required
def unfollow(username):
    try:
        to_user = models.User.get(models.User.username ** username)
    except models.DoesNotExist:
        pass
    else:
        try:
            models.Relationship.get(
                from_user=g.user._get_current_object(),
                to_user=to_user
            ).delete_instance()
        except models.IntegrityError:
            pass
        else:
            flash("You've unfollowed {}".format(to_user.username), 'success')

    return redirect(url_for('stream', username=to_user.username))

if __name__ == '__main__':
    models.initialize()
    app.run(debug=DEBUG, host=HOST, port=PORT)