from datetime import datetime
from extensions import db


class SavedJob(db.Model):
    __tablename__ = 'saved_jobs'

    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id', ondelete='CASCADE'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        db.UniqueConstraint('candidate_id', 'job_id', name='uq_candidate_job_saved'),
    )

    def __repr__(self):
        return f'<SavedJob candidate_id={self.candidate_id} job_id={self.job_id}>'
