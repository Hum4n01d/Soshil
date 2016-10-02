from hashlib import md5
from os import environ

import requests
from flask import Blueprint, flash, redirect, url_for, render_template, request, g
from flask_login import login_required, logout_user, login_user
from flask_bcrypt import check_password_hash

import forms
import models

accounts_blueprint = Blueprint('accounts', __name__, url_prefix='/accounts')

@accounts_blueprint.route('/sign_up', methods=('GET', 'POST'))
def sign_up():
    form = forms.RegisterForm()

    if form.validate_on_submit():

        email = form.email.data.lower().encode('utf-8')
        gravatar_url = 'https://www.gravatar.com/avatar/' + md5(email).hexdigest() + '?d=retro&s=75'

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

@accounts_blueprint.route('/log_in', methods=('GET', 'POST'))
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
                    flash('Your username or password is incorrect', 'error')

    return render_template('log_in.html', form=form)

@accounts_blueprint.route('/log_in/github')
def github_oauth():
    CLIENT_ID = environ['CLIENT_ID']
    return redirect('https://github.com/login/oauth/authorize?scope=user:email&client_id=' + CLIENT_ID)

@accounts_blueprint.route('/log_in/github/callback')
def github_oauth_callback():
    code = request.args.get('code')
    response = requests.post('https://github.com/login/oauth/access_token', {
        "client_id": environ['CLIENT_ID'],
        "client_secret": environ['CLIENT_SECRET'],
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

    try:
        login_user(user=models.User.get(models.User.email == email))
    except models.DoesNotExist:
        user = models.User.create_user(
            username=username,
            email=email.lower(),
            password='',
            avatar_url=avatar_url,
            github_user=True
        )

        login_user(user)

    flash("You've been logged in!", "success")

    return redirect(url_for('index'))

@accounts_blueprint.route('/log_out')
@login_required
def log_out():
    logout_user()
    flash('You\'ve been logged out.', 'success')
    return redirect(url_for('accounts.log_in'))

@accounts_blueprint.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
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

@accounts_blueprint.route('/delete_my_account', methods=['GET', 'POST'])
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

@accounts_blueprint.route('/delete_my_posts', methods=['GET', 'POST'])
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

            return redirect(url_for('index'))
        else:
            flash('You entered your username wrong', 'error')

    return render_template('confirm_delete.html', form=form, case='Post')

@accounts_blueprint.route('/delete_my_comments', methods=['GET', 'POST'])
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
            return redirect(url_for('index'))
        else:
            flash('You entered your username wrong', 'error')

    return render_template('confirm_delete.html', form=form, case='Comment')