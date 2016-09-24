import os
import hashlib
import requests

from flask import Flask, g, render_template, flash, redirect, url_for, request, abort
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt, check_password_hash
from flaskext.markdown import Markdown

import forms
import models

app = Flask(__name__)
app.secret_key = 'rw8efuhjeqr38efygduvbefjkqgiuwohv3k2r112qwfay98qughgiuwr23tw89ry0f'

RECAPTCHA_PUBLIC_KEY = os.environ['SOSHIL_RECAPTCHA_PUBLIC_KEY']
RECAPTCHA_PRIVATE_KEY = os.environ['SOSHIL_RECAPTCHA_PRIVATE_KEY']
app.config.from_object(__name__)

bcrypt = Bcrypt(app)

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
    return render_template('error.html', num=404), 404

@app.errorhandler(401)
def unauthorized(error):
    return render_template('error.html', num=401), 401

@app.errorhandler(500)
def internal_server_error(error):
    return render_template('error.html', num=500), 500

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
            models.Notification.create_notification(
                title='Welcome to Soshil!',
                link=url_for('welcome'),
                user=g.user._get_current_object()
            )

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
    if g.user._get_current_object().is_authenticated:
        return redirect('stream')
    else:
        return render_template('index.html')

@app.route('/all')
def all_posts():
    stream = models.Post.select().limit(100)

    return render_template('stream.html', stream=stream, public=True)

@app.route('/welcome')
@login_required
def welcome():
    return render_template('welcome.html')

@app.route('/explore')
@login_required
def explore():
    try:
        users_following = g.user._get_current_object().following()

        users_following_users_following = []

        for user in users_following:
            users_following_users_following.append(user.following())

        stream = models.Post.select().where(
            models.Post.user << users_following_users_following,
            models.Post.user != g.user._get_current_object()
        ).limit(100)

    except models.DoesNotExist:
        stream = None
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
        content = models.parse_post(form.content.data, page=url_for('view_post', post_id=post_id))

        models.Comment.create(
            user=g.user._get_current_object(),
            post=post,
            content=content
        )

        if not g.user._get_current_object() == post.user:
            models.Notification.create_notification(
                title='@{} commented on your post!'.format(g.user._get_current_object().username),
                link=url_for('view_post', post_id=post_id),
                user=post.user
            )

        return redirect(url_for('view_post', post_id=post_id))

    else:
        if not post:
            abort(404)

    return render_template('post.html', post=post, comments=comments, form=form)

@app.route('/post/<int:post_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    try:
        post = models.Post.get(models.Post.id == post_id)

    except models.DoesNotExist:
        abort(404)

    user = g.user._get_current_object()

    if user.is_admin or post.user == user:
        form = forms.PostForm()

        if form.validate_on_submit():
            raw_content = form.content.data.strip()

            q = models.Post.update(
                title=form.title.data,
                raw_content=raw_content,
                content=models.parse_post(raw_content, page=url_for('view_post', post_id=post_id), edit=True)
            ).where(models.Post.id == post_id)
            q.execute()

            return redirect(url_for('view_post', post_id=post_id))

        else:
            form.title.data = post.title
            form.content.data = post.raw_content
    else:
        abort(401)

    return render_template('post_editor.html', form=form, edit=True)

@app.route('/new_post', methods=['GET', 'POST'])
@login_required
def new_post():
    form = forms.PostForm()

    if form.validate_on_submit():
        raw_content = form.content.data.strip()

        p = models.Post.create(
            user=g.user._get_current_object(),
            title=form.title.data.strip(),
            raw_content=raw_content,
            content=raw_content
        )

        models.Post.update(
            content=models.parse_post(raw_content, page=url_for('view_post', post_id=p.id))
        ).where(models.Post.id == p.id).execute()

        flash('Message successfully posted!', 'success')
        return redirect(url_for('index'))

    return render_template('post_editor.html', form=form)

@app.route('/follow/<username>')
@login_required
def follow(username):
    if username.lower() == g.user._get_current_object().username.lower():
        flash("You can't follow yourself! Nice try though")
        return redirect(url_for('profile', username=g.user._get_current_object().username))
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
                username = g.user._get_current_object().username
                models.Notification.create_notification(
                    title='@{} is now following you!'.format(username),
                    link=url_for('profile', username=username),
                    user=to_user
                )
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
        user = g.user._get_current_object()

        if to_user == user:
            flash('Why are you unfollowing yourself? Nice try.')
            return redirect(url_for('profile', username=user.username))
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

    user = g.user._get_current_object()

    if post.user == user or user.is_admin:
        if models.Comment.select().where(models.Comment.post == post).exists():
            models.Comment.delete().where(models.Comment.post == post).execute()

        post.delete_instance()

    else:
        abort(401)

    flash('Post deleted!', 'sucess')
    return redirect(url_for('index'))

@app.route('/delete_comment')
def delete_comment():
    comment_id = request.args.get('comment_id')

    try:
        comment = models.Comment.get(models.Comment.id == comment_id)
    except models.DoesNotExist:
        abort(404)


    try:
        user = g.user._get_current_object()

        if comment.user == user or user.is_admin:
            comment.delete_instance()

        else:
            abort(401)

        flash('Comment deleted!', 'sucess')
        return redirect(url_for('view_post', post_id=comment.post.id))

    except models.DoesNotExist:
        abort(404)

@app.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    form = forms.AccountForm()
    user = g.user._get_current_object()

    if form.validate_on_submit():
        email = form.email.data
        avatar_url = form.avatar_url.data

        if email and not email == user.email:
            models.User.update(email=email).where(models.User.id == user.id).execute()

        if avatar_url and not avatar_url == user.avatar_url:
            models.User.update(avatar_url=form.avatar_url.data).where(models.User.id == user.id).execute()

        flash('Your account settings were updated')

    return render_template('account.html', form=form)

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/delete_my_account', methods=['GET', 'POST'])
@login_required
def delete_my_account():
    form = forms.DeleteForm()
    user = g.user._get_current_object()

    if form.validate_on_submit():
        if form.username.data == user.username:
            models.User.delete().where(
                models.User.id == user.id
            ).execute()

            models.Post.delete().where(
                models.Post.user == user
            ).execute()

            models.Comment.delete().where(
                models.Comment.user == user
            ).execute()

            flash('Your account was deleted')
        else:
            flash('You entered your username wrong', 'error')

    return render_template('confirm_delete.html', form=form, case='Account')

@app.route('/delete_my_posts', methods=['GET', 'POST'])
@login_required
def delete_my_posts():
    form = forms.DeleteForm()
    user = g.user._get_current_object()

    if form.validate_on_submit():
        if form.username.data == user.username:
            posts = models.Post.select().where(models.Post.user == user)

            for post in posts:
                models.Comment.delete().where(
                    models.Comment.post == post
                ).execute()

                post.delete_instance()

            flash('Your posts were deleted')
        else:
            flash('You entered your username wrong', 'error')

    return render_template('confirm_delete.html', form=form, case='Post')

@app.route('/delete_my_comments', methods=['GET', 'POST'])
@login_required
def delete_my_comments():
    form = forms.DeleteForm()
    user = g.user._get_current_object()

    if form.validate_on_submit():
        if form.username.data == user.username:
            models.Comment.delete().where(
                models.Comment.user == user
            ).execute()

            flash('Your comments were deleted')
        else:
            flash('You entered your username wrong', 'error')

    return render_template('confirm_delete.html', form=form, case='Comment')

@app.route('/notifications')
@login_required
def notifications():
    try:
        notifications = models.Notification.select().where(models.Notification.user == g.user._get_current_object())
    except models.DoesNotExist:
        notifications = None

    for notification in notifications:
        notification.delete_instance()

    return render_template('notifications.html', notifications=notifications)

@app.route('/get_notifications')
def get_notifications():
    user = g.user._get_current_object()

    if user.is_authenticated:
        notification_count = models.Notification.select().where(models.Notification.user == user).count()

    else:
        notification_count = 0

    return str(notification_count)

@app.route('/admin')
@login_required
def admin():
    if g.user._get_current_object().is_admin:
        pass
    else:
        abort(401)

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