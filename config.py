import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-jobportal-2026-key-antigravity'
    
    # Database config: defaults to SQLite database.db in project root
    # Ready for future migration to PostgreSQL / MySQL via DATABASE_URL
    db_url = os.environ.get('DATABASE_URL')
    if db_url and db_url.startswith('postgres://'):
        # Fix legacy postgresql uri format
        db_url = db_url.replace('postgres://', 'postgresql://', 1)
        
    SQLALCHEMY_DATABASE_URI = db_url or ('sqlite:///' + os.path.join(basedir, 'database.db'))
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Uploads configuration
    UPLOAD_FOLDER = os.path.join(basedir, 'uploads')
    RESUME_FOLDER = os.path.join(UPLOAD_FOLDER, 'resumes')
    PHOTO_FOLDER = os.path.join(UPLOAD_FOLDER, 'profile_photos')
    LOGO_FOLDER = os.path.join(UPLOAD_FOLDER, 'company_logos')

    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH') or (16 * 1024 * 1024))  # 16 MB max
    ALLOWED_RESUME_EXTENSIONS = {'pdf', 'doc', 'docx', 'rtf', 'txt'}
    ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'gif', 'bmp', 'jfif', 'svg'}

    # Pagination
    JOBS_PER_PAGE = 9
    ADMIN_PER_PAGE = 15
