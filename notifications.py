from flask import Blueprint, render_template, g
from flask_login import login_required

notifications_blueprint = Blueprint('notifications', __name__, url_prefix='/notifications')

import models

@notifications_blueprint.route('/')
@login_required
def view():
    try:
        notifications = models.Notification.select().where(models.Notification.user == g.user._get_current_object())
    except models.DoesNotExist:
        notifications = None

    for notification in notifications:
        notification.delete_instance()

    return render_template('notifications.html', notifications=notifications)

@notifications_blueprint.route('/get')
@login_required
def get():
    user = g.user._get_current_object()

    if user.is_authenticated:
        notification_count = models.Notification.select().where(models.Notification.user == user).count()

    else:
        notification_count = 0

    return str(notification_count)