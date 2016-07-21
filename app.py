import os
import hashlib

import requests

from flask import Flask, g, render_template, flash, redirect, url_for, request, abort
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt, check_password_hash

import forms
import models

app = Flask(__name__)
app.secret_key = 'rw8efuhjeqr38efygduvbefjkqgiuwohv3k2r112qwfay98qughgiuwr23tw89ry0f'

bcrypt = Bcrypt(app)

DEBUG = True
PORT = int(os.environ.get('PORT', 8000))
HOST = '0.0.0.0'

@app.context_processor
def inject_user():
    return dict(user=g.user._get_current_object())

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.session_protection = 'strong'
login_manager.login_view = 'log_in'

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
    return render_template('error.html', error=error), 404

@app.errorhandler(401)
def unauthorized(error):
    return render_template('error.html', error=error), 401

@app.route('/sign_up', methods=('GET', 'POST'))
def sign_up():
    form = forms.RegisterForm()

    if form.validate_on_submit():
        email = form.email.data.lower().encode('utf-8')
        gravatar_url = 'https://www.gravatar.com/avatar/' + hashlib.md5(email).hexdigest() + '?d=retro&s=75'

        try:
            models.User.create_user(
                username=form.username.data,
                email=email,
                password=form.password.data,
                avatar_url=gravatar_url
            )
            login_user(models.User.get(models.User.username ** form.username.data.lower()))
            flash('You\'ve been successfully registered!', 'success')

            return redirect(url_for('index'))

        except:
            flash('Username already exists')

    return render_template('sign_up.html', form=form)

@app.route('/log_in', methods=('GET', 'POST'))
def log_in():
    form = forms.LoginForm()
    next_url = request.args.get('next')

    if form.validate_on_submit():
        try:
            user = models.User.get(models.User.username ** form.username.data.lower())
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

    return render_template('log_in.html', form=form)

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

    user_json = requests.get('https://api.github.com/user', {"access_token": access_token}).json()
    username = user_json['login']
    avatar_url = user_json['avatar_url']
    emails = requests.get('https://api.github.com/user/emails', {"access_token": access_token}).json()
    email = ''

    for address in emails:
        if address['primary']:
            if address['verified']:
                email = address['email']
                break
            else:
                flash('Please verify your Github account', 'error')
                break

    del emails, access_token, code, address, user_json

    try:
        login_user(user=models.User.get(models.User.email == email))
    except models.DoesNotExist:
        models.User.create_user(
            username=username,
            email=email.lower(),
            password='',
            avatar_url=avatar_url,
            github_user=True
        )

    login_user(user = models.User.get(models.User.email == email))
    flash("You've been logged in!", "success")

    return redirect(url_for('index'))

@app.route('/log_out')
@login_required
def log_out():
    logout_user()
    flash('You\'ve been logged out.', 'success')
    return redirect(url_for('log_in'))

@app.route('/')
def index():
    stream = models.Post.select().limit(100)
    return render_template('index.html', stream=stream, public=True)

@app.route('/explore')
@login_required
def explore():
    users_following = g.user._get_current_object().following()
    users_following_users_following = []

    for user in users_following:
        users_following_users_following.append(user.following())

    stream = models.Post.select().where(
        models.Post.user << users_following_users_following
    ).limit(100)
    return render_template('stream.html', stream=stream, explore=True)

@app.route('/users/<username>')
def profile(username):
    try:
        profile_user = models.User.select().where(models.User.username ** username).get()
        stream = profile_user.posts.limit(100)

    except models.DoesNotExist:
        abort(404)

    return render_template('profile.html', profile_user=profile_user, stream=stream)

@app.route('/users/<username>/followers')
def followers(username):
    try:
        profile_user = models.User.select().where(models.User.username ** username).get()
        followers = profile_user.followers()

    except models.DoesNotExist:
        abort(404)

    return render_template('followers.html', profile_user=profile_user, stream=stream, user_list=followers)

@app.route('/users/<username>/following')
def following(username):
    try:
        profile_user = models.User.select().where(models.User.username ** username).get()
        following = profile_user.following()

    except models.DoesNotExist:
        abort(404)

    return render_template('following.html', profile_user=profile_user, stream=stream, user_list=following)

@app.route('/stream')
@login_required
def stream():
    stream = current_user.get_stream().limit(100)

    return render_template('stream.html', stream=stream)

@app.route('/post/<int:post_id>', methods=['GET', 'POST'])
def view_post(post_id):
    form = forms.CommentForm()

    try:
        post = models.Post.select().where(models.Post.id == post_id).get()
    except models.DoesNotExist:
        abort(404)

    comments = models.Comment.select().where(models.Comment.post == post)

    if form.validate_on_submit():
        models.Comment.create(
            user=g.user._get_current_object(),
            post=post,
            content=form.content.data
        )
        return redirect(url_for('view_post', post_id=post_id))

    else:
        if not post:
            abort(404)

    return render_template('post.html', post=post, comments=comments, form=form)

@app.route('/new_post', methods=('GET', 'POST'))
@login_required
def new_post():
    form = forms.PostForm()
    if form.validate_on_submit():
        models.Post.create(
            user=g.user._get_current_object(),
            title=form.title.data,
            content=form.content.data.strip()
        )
        flash('Message successfully posted!', 'success')
        return redirect(url_for('index'))
    
    return render_template('new_post.html', form=form)

@app.route('/follow/<username>')
@login_required
def follow(username):
    if username.lower() == g.user._get_current_object().username.lower():
        flash("You can't follow yourself!")
        return redirect(url_for('stream'))
    else:
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

        return redirect(url_for('profile', username=to_user.username))

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

    return redirect(url_for('profile', username=to_user.username))

@app.route('/delete_post')
def delete_post():
    post_id = request.args.get('post_id')

    try:
        post = models.Post.get(models.Post.id == post_id)
    except models.DoesNotExist:
        abort(404)

    try:
        if post.user == g.user._get_current_object():
            try:
                models.Comment.get(models.Comment.post == post).delete_instance()
            except models.DoesNotExist:
                pass

            post.delete_instance()

        else:
            abort(401)

        flash('Post deleted!', 'sucess')
        return redirect(url_for('index'))

    except models.DoesNotExist:
        abort(404)

@app.route('/delete_comment')
def delete_comment():
    comment_id = request.args.get('comment_id')
    comment = models.Comment.get(models.Comment.id == comment_id)
    post_id = comment.post.id

    try:
        if comment.user == g.user._get_current_object():
            comment.delete_instance()

        else:
            abort(401)

        flash('Comment deleted!', 'sucess')
        return redirect(url_for('view_post', post_id=post_id))

    except models.DoesNotExist:
        abort(404)

@app.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    return render_template('account.html')

@app.route('/terms')
def terms():
    return render_template('terms.html')

if __name__ == '__main__':
    models.initialize()

    extra_dirs = ['templates/*']
    extra_files = extra_dirs[:]
    for extra_dir in extra_dirs:
        for dirname, dirs, files in os.walk(extra_dir):
            for filename in files:
                filename = os.path.join(dirname, filename)
                if os.path.isfile(filename):
                    extra_files.append(filename)
    app.extra_files = extra_files

    app.run(host=HOST, port=PORT, debug=DEBUG)