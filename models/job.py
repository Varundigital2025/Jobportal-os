from datetime import datetime, date
from extensions import db


class Job(db.Model):
    __tablename__ = 'jobs'

    id = db.Column(db.Integer, primary_key=True)
    employer_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id', ondelete='CASCADE'), nullable=True)
    title = db.Column(db.String(150), nullable=False, index=True)
    description = db.Column(db.Text, nullable=False)
    requirements = db.Column(db.Text, nullable=True)
    responsibilities = db.Column(db.Text, nullable=True)
    location = db.Column(db.String(150), nullable=False, index=True)
    job_type = db.Column(db.String(50), nullable=False)  # Full Time, Part Time, Contract, Internship, Freelance
    work_mode = db.Column(db.String(50), nullable=False)  # On-site, Remote, Hybrid
    experience_level = db.Column(db.String(50), nullable=True)  # Entry Level, Mid Level, Senior Level, Lead
    salary_min = db.Column(db.Integer, nullable=True)
    salary_max = db.Column(db.Integer, nullable=True)
    salary_currency = db.Column(db.String(10), default='₹', nullable=False)
    skills = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(100), nullable=False, index=True)
    deadline = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(20), default='Open', nullable=False)  # Open, Closed, Draft
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    applications = db.relationship('Application', backref='job', cascade='all, delete-orphan')
    saved_by = db.relationship('SavedJob', backref='job', cascade='all, delete-orphan')

    @property
    def skills_list(self):
        if not self.skills:
            return []
        return [s.strip() for s in self.skills.split(',') if s.strip()]

    @property
    def formatted_salary(self):
        cur = self.salary_currency or '₹'
        if self.salary_min and self.salary_max:
            return f"{cur}{self.salary_min:,} - {cur}{self.salary_max:,}"
        elif self.salary_min:
            return f"From {cur}{self.salary_min:,}"
        elif self.salary_max:
            return f"Up to {cur}{self.salary_max:,}"
        return "Competitive"

    @property
    def is_open(self):
        return self.status == 'Open'

    @property
    def applicant_count(self):
        return len(self.applications)

    def __repr__(self):
        return f'<Job {self.id}: {self.title}>'
