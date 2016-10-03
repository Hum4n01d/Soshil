from flask import abort, render_template, flash, redirect, Blueprint, url_for, g
from flask_login import login_required

import models

users_blueprint = Blueprint('users', __name__, url_prefix='/users')

@users_blueprint.route('/<username>')
def profile(username):
    try:
        profile_user = models.User.select().where(models.User.username ** username).get()
        stream = profile_user.posts.limit(100)

    except models.DoesNotExist:
        flash('That user doesn\'t exist', 'error')
        abort(404)

    return render_template('profile.html', profile_user=profile_user, stream=stream)

@users_blueprint.route('/<username>/followers')
def followers(username):
    try:
        profile_user = models.User.select().where(models.User.username ** username).get()
        followers = profile_user.followers()

    except models.DoesNotExist:
        flash('That user doesn\'t exist', 'error')
        abort(404)

    return render_template('followers.html', profile_user=profile_user, user_list=followers)

@users_blueprint.route('/<username>/following')
def following(username):
    try:
        profile_user = models.User.select().where(models.User.username ** username).get()
        following = profile_user.following()

    except models.DoesNotExist:
        flash('That user doesn\'t exist', 'error')
        abort(404)

    return render_template('following.html', profile_user=profile_user, user_list=following)

@users_blueprint.route('/<username>/follow')
@login_required
def follow(username):
    if username.lower() == g.user._get_current_object().username.lower():
        flash("You can't follow yourself! Nice try though")
        return redirect(url_for('users.profile', username=g.user._get_current_object().username))

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
                    link=url_for('users.profile', username=username),
                    user=to_user
                )
                flash("You're now following {}".format(to_user.username), 'success')

        return redirect(url_for('users.profile', username=to_user.username))

@users_blueprint.route('/<username>/unfollow')
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
            return redirect(url_for('users.profile', username=user.username))
        try:
            models.Relationship.get(
                from_user=g.user._get_current_object(),
                to_user=to_user
            ).delete_instance()
        except models.IntegrityError:
            pass
        else:
            flash("You've unfollowed {}".format(to_user.username), 'success')

    return redirect(url_for('users.profile', username=to_user.username))