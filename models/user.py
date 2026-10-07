from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'candidate', 'employer', 'admin'
    phone = db.Column(db.String(30), nullable=True)
    location = db.Column(db.String(150), nullable=True)
    profile_photo = db.Column(db.String(255), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    candidate_profile = db.relationship('CandidateProfile', backref='user', uselist=False, cascade='all, delete-orphan')
    company = db.relationship('Company', backref='employer', uselist=False, cascade='all, delete-orphan')
    posted_jobs = db.relationship('Job', backref='employer', cascade='all, delete-orphan', foreign_keys='Job.employer_id')
    applications = db.relationship('Application', backref='candidate', cascade='all, delete-orphan', foreign_keys='Application.candidate_id')
    saved_jobs = db.relationship('SavedJob', backref='candidate', cascade='all, delete-orphan', foreign_keys='SavedJob.candidate_id')
    notifications = db.relationship('Notification', backref='user', cascade='all, delete-orphan', order_by='Notification.created_at.desc()')

    @property
    def unread_notifications_count(self):
        return sum(1 for n in self.notifications if not n.is_read)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_candidate(self):
        return self.role == 'candidate'

    @property
    def is_employer(self):
        return self.role == 'employer'

    @property
    def is_admin(self):
        return self.role == 'admin'

    def __repr__(self):
        return f'<User {self.email} ({self.role})>'
