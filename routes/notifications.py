from flask import Blueprint, render_template, request, redirect, url_for, flash
from services.auth_service import login_required, get_current_user
from services.notification_service import (
    get_user_notifications,
    mark_notification_as_read,
    mark_all_notifications_as_read
)

notifications_bp = Blueprint('notifications', __name__, url_prefix='/notifications')


@notifications_bp.route('/')
@login_required
def list_notifications():
    user = get_current_user()
    notifications = get_user_notifications(user.id, limit=50)
    return render_template('notifications.html', user=user, notifications=notifications)


@notifications_bp.route('/<int:notif_id>/read', methods=['POST'])
@login_required
def mark_read(notif_id):
    user = get_current_user()
    mark_notification_as_read(notif_id, user.id)
    target_url = request.form.get('redirect_to')
    if target_url and target_url.startswith('/'):
        return redirect(target_url)
    return redirect(request.referrer or url_for('notifications.list_notifications'))


@notifications_bp.route('/read-all', methods=['POST'])
@login_required
def mark_all_read():
    user = get_current_user()
    mark_all_notifications_as_read(user.id)
    flash('All notifications marked as read.', 'success')
    return redirect(request.referrer or url_for('notifications.list_notifications'))
