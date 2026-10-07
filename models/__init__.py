from extensions import db
from models.user import User
from models.candidate import CandidateProfile
from models.company import Company
from models.job import Job
from models.application import Application
from models.saved_job import SavedJob
from models.notification import Notification
from models.system_setting import SystemSetting

__all__ = [
    'db',
    'User',
    'CandidateProfile',
    'Company',
    'Job',
    'Application',
    'SavedJob',
    'Notification',
    'SystemSetting'
]

