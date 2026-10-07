from extensions import db
from models.notification import Notification
from models.user import User


def create_notification(user_id, title, message, link=None):
    """Creates a new notification record for a specific user."""
    if not user_id:
        return None
    notif = Notification(
        user_id=user_id,
        title=title,
        message=message,
        link=link,
        is_read=False
    )
    db.session.add(notif)
    db.session.commit()
    return notif


def notify_admin(title, message, link=None):
    """Sends a notification to the platform administrator."""
    admin = User.query.filter_by(role='admin').first()
    if admin:
        return create_notification(admin.id, title, message, link)
    return None


def get_user_notifications(user_id, limit=25):
    """Retrieves notifications for a given user ordered by newest first."""
    return Notification.query.filter_by(user_id=user_id)\
        .order_by(Notification.created_at.desc())\
        .limit(limit)\
        .all()


def mark_notification_as_read(notification_id, user_id):
    """Marks a single notification as read if it belongs to the user."""
    notif = db.session.get(Notification, notification_id)
    if notif and notif.user_id == user_id:
        notif.is_read = True
        db.session.commit()
        return True
    return False


def mark_all_notifications_as_read(user_id):
    """Marks all unread notifications for a user as read."""
    Notification.query.filter_by(user_id=user_id, is_read=False)\
        .update({Notification.is_read: True})
    db.session.commit()
    return True
