from datetime import datetime
from extensions import db


class SystemSetting(db.Model):
    """
    Key-Value storage for dynamic platform and admin portal configuration.
    Enables zero-code runtime customization of branding, logos, details,
    API integrations, and platform controls.
    """
    __tablename__ = 'system_settings'

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False, index=True)
    value = db.Column(db.Text, nullable=True)
    group = db.Column(db.String(50), default='general', nullable=False)  # 'admin_portal', 'general', 'integration', 'security'
    description = db.Column(db.String(255), nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f'<SystemSetting {self.key}={self.value[:30] if self.value else "None"}>'
