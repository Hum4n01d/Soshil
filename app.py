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
    g.db = models.DATABASE
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
            user = models.User.get(models.User.username == form.username.data)
            
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
    return render_template('index.html', user=g.user)

@app.route('/new_post', methods=('GET', 'POST'))
@login_required
def post():
    form = forms.PostForm()
    if form.validate_on_submit():
        models.Post.create(user=g.user, content=form.content.data.strip())
        flash('Message successfully posted!', 'success')
        return redirect(url_for('index'))
    
    return render_template('post.html', form=form, user=g.user)

@app.route('/users/<username>')
def users(username):
    try:
        user = models.User.get(models.User.low_username == username.lower())
    except models.DoesNotExist:
        user = None
        
    return render_template('profile.html', user=user)

if __name__ == '__main__':
    models.initialize()
    app.run(debug=DEBUG, host=HOST, port=PORT)