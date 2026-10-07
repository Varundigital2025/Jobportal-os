import os
import sys
from flask import Flask, render_template, send_from_directory, abort, session, redirect, url_for
from config import Config
from extensions import db
from models.user import User
from models.candidate import CandidateProfile
from models.company import Company
from models.job import Job
from models.application import Application
from models.saved_job import SavedJob
from models.system_setting import SystemSetting
from services.auth_service import get_current_user, login_required
from services.job_service import get_popular_categories, get_featured_jobs, get_top_companies
from services.settings_service import get_all_settings, init_default_settings

# Import Blueprints
from routes.auth import auth_bp
from routes.jobs import jobs_bp
from routes.candidate import candidate_bp
from routes.employer import employer_bp
from routes.admin import admin_bp
from routes.notifications import notifications_bp


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)

    # Ensure required upload folders exist
    os.makedirs(app.config['RESUME_FOLDER'], exist_ok=True)
    os.makedirs(app.config['PHOTO_FOLDER'], exist_ok=True)
    os.makedirs(app.config['LOGO_FOLDER'], exist_ok=True)
    os.makedirs(app.config.get('BRANDING_FOLDER', os.path.join(app.config['UPLOAD_FOLDER'], 'branding')), exist_ok=True)

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(jobs_bp)
    app.register_blueprint(candidate_bp)
    app.register_blueprint(employer_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(notifications_bp)

    # Global Template Context Processor
    @app.context_processor
    def inject_global_variables():
        user = get_current_user()
        saved_count = 0
        unread_notifs = 0
        if user:
            from models.notification import Notification
            unread_notifs = Notification.query.filter_by(user_id=user.id, is_read=False).count()
            if user.role == 'candidate':
                saved_count = SavedJob.query.filter_by(candidate_id=user.id).count()
        return dict(
            current_user=user,
            user_saved_jobs_count=saved_count,
            unread_notifications_count=unread_notifs,
            site_settings=get_all_settings()
        )

    # Public Homepage
    @app.route('/')
    def home():
        categories = get_popular_categories(limit=8)
        featured_jobs = get_featured_jobs(limit=6)
        top_companies = get_top_companies(limit=6)
        total_jobs_count = Job.query.filter_by(status='Open').count()
        total_companies_count = Company.query.count()
        return render_template(
            'home.html',
            categories=categories,
            featured_jobs=featured_jobs,
            top_companies=top_companies,
            total_jobs_count=total_jobs_count,
            total_companies_count=total_companies_count
        )

    # About Page
    @app.route('/about')
    def about():
        return render_template('about.html')

    # Uploads Delivery Routes
    @app.route('/uploads/profile_photos/<path:filename>')
    def serve_profile_photo(filename):
        return send_from_directory(app.config['PHOTO_FOLDER'], filename)

    @app.route('/uploads/company_logos/<path:filename>')
    def serve_company_logo(filename):
        return send_from_directory(app.config['LOGO_FOLDER'], filename)

    @app.route('/uploads/branding/<path:filename>')
    def serve_branding_logo(filename):
        return send_from_directory(app.config.get('BRANDING_FOLDER', os.path.join(app.config['UPLOAD_FOLDER'], 'branding')), filename)

    @app.route('/uploads/resumes/<path:filename>')
    @login_required
    def serve_resume(filename):
        user = get_current_user()
        # Security: Allow only if candidate owns resume, employer has an applicant with this resume, or user is admin
        is_candidate_owner = (
            user.role == 'candidate' and
            user.candidate_profile and
            user.candidate_profile.resume_path == filename
        )
        is_admin = (user.role == 'admin')
        is_applicant_resume = False
        if user.role == 'employer':
            is_applicant_resume = Application.query.join(Job).filter(
                Application.resume_path == filename,
                Job.employer_id == user.id
            ).first() is not None

        if not (is_candidate_owner or is_admin or is_applicant_resume):
            abort(403)

        return send_from_directory(app.config['RESUME_FOLDER'], filename)

    # Error Handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('errors/403.html'), 403

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500

    # Create tables automatically on startup if they don't exist
    with app.app_context():
        db.create_all()
        # Ensure default system settings exist
        try:
            init_default_settings()
        except Exception:
            pass
        # Safe column upgrade for existing SQLite databases
        try:
            from sqlalchemy import inspect, text
            inspector = inspect(db.engine)
            if 'applications' in inspector.get_table_names():
                existing_cols = {col['name'] for col in inspector.get_columns('applications')}
                new_app_cols = [
                    ('applicant_name', 'VARCHAR(100)'),
                    ('applicant_email', 'VARCHAR(120)'),
                    ('applicant_phone', 'VARCHAR(30)'),
                    ('applicant_location', 'VARCHAR(150)'),
                    ('experience', 'VARCHAR(255)'),
                    ('qualification', 'VARCHAR(150)'),
                    ('skills', 'TEXT'),
                    ('admin_notes', 'TEXT'),
                ]
                with db.engine.connect() as conn:
                    for col_name, col_type in new_app_cols:
                        if col_name not in existing_cols:
                            conn.execute(text(f'ALTER TABLE applications ADD COLUMN {col_name} {col_type}'))
                    conn.commit()
        except Exception:
            pass

    return app


app = create_app()

if __name__ == '__main__':
    # Support python app.py --init-db
    if '--init-db' in sys.argv:
        with app.app_context():
            db.create_all()
            print("Database tables verified/created successfully.")
        sys.exit(0)

    print("\n" + "="*50)
    print(" JobPortal Server Running on Windows")
    print(" Access at: http://127.0.0.1:5000")
    print("="*50 + "\n")
    app.run(host='127.0.0.1', port=5000, debug=True)
