from datetime import datetime
from extensions import db


class CandidateProfile(db.Model):
    __tablename__ = 'candidate_profiles'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False)
    headline = db.Column(db.String(150), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    skills = db.Column(db.Text, nullable=True)
    experience = db.Column(db.Text, nullable=True)
    education = db.Column(db.Text, nullable=True)
    qualification = db.Column(db.String(150), nullable=True)
    resume_filename = db.Column(db.String(255), nullable=True)
    resume_path = db.Column(db.String(255), nullable=True)
    linkedin_url = db.Column(db.String(255), nullable=True)
    portfolio_url = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    @property
    def skills_list(self):
        if not self.skills:
            return []
        return [s.strip() for s in self.skills.split(',') if s.strip()]

    @property
    def completion_percentage(self):
        # Calculate percentage based on 10 profile elements
        fields = [
            bool(self.user.name),
            bool(self.user.phone),
            bool(self.user.location),
            bool(self.user.profile_photo),
            bool(self.headline),
            bool(self.bio),
            bool(self.skills),
            bool(self.experience),
            bool(self.education or self.qualification),
            bool(self.resume_path)
        ]
        completed = sum(1 for f in fields if f)
        return int((completed / len(fields)) * 100)

    def __repr__(self):
        return f'<CandidateProfile user_id={self.user_id}>'
