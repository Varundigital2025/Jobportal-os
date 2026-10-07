from datetime import datetime
from extensions import db


class Company(db.Model):
    __tablename__ = 'companies'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False)
    company_name = db.Column(db.String(150), nullable=False)
    logo = db.Column(db.String(255), nullable=True)
    description = db.Column(db.Text, nullable=True)
    industry = db.Column(db.String(100), nullable=True)
    company_size = db.Column(db.String(50), nullable=True)  # e.g. '1-10', '11-50', '51-200', '201-500', '500+'
    website = db.Column(db.String(255), nullable=True)
    location = db.Column(db.String(150), nullable=True)
    phone = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    jobs = db.relationship('Job', backref='company', cascade='all, delete-orphan')

    @property
    def active_jobs_count(self):
        return sum(1 for j in self.jobs if j.status == 'Open')

    def __repr__(self):
        return f'<Company {self.company_name}>'
