from datetime import datetime
from extensions import db


class Application(db.Model):
    __tablename__ = 'applications'

    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id', ondelete='CASCADE'), nullable=False)
    candidate_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    
    # Applicant details captured at submission
    applicant_name = db.Column(db.String(100), nullable=True)
    applicant_email = db.Column(db.String(120), nullable=True)
    applicant_phone = db.Column(db.String(30), nullable=True)
    applicant_location = db.Column(db.String(150), nullable=True)
    experience = db.Column(db.String(255), nullable=True)
    qualification = db.Column(db.String(150), nullable=True)
    skills = db.Column(db.Text, nullable=True)

    resume_path = db.Column(db.String(255), nullable=True)
    cover_letter = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(30), default='Applied', nullable=False)
    # Statuses: 'Applied', 'Under Review', 'Shortlisted', 'Interview', 'Rejected', 'Selected'
    admin_notes = db.Column(db.Text, nullable=True)
    applied_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        db.UniqueConstraint('job_id', 'candidate_id', name='uq_job_candidate_application'),
    )

    @property
    def status_badge_class(self):
        classes = {
            'Applied': 'badge-primary',
            'Under Review': 'badge-warning',
            'Shortlisted': 'badge-info',
            'Interview': 'badge-purple',
            'Rejected': 'badge-danger',
            'Selected': 'badge-success',
        }
        return classes.get(self.status, 'badge-neutral')

    def __repr__(self):
        return f'<Application id={self.id} job_id={self.job_id} candidate_id={self.candidate_id}>'
