import os
import uuid
from functools import wraps
from flask import session, redirect, url_for, flash, request, abort, current_app
from werkzeug.utils import secure_filename
from extensions import db
from models.user import User
from models.candidate import CandidateProfile
from models.company import Company


def login_user(user, remember=False):
    """Log user in by setting session variables."""
    session.clear()
    session['user_id'] = user.id
    session['role'] = user.role
    session['user_name'] = user.name
    session['user_email'] = user.email
    if remember:
        session.permanent = True


def logout_user():
    """Clear session data."""
    session.clear()


def get_current_user():
    """Retrieve currently authenticated user from database, if any."""
    user_id = session.get('user_id')
    if not user_id:
        return None
    user = db.session.get(User, user_id)
    if not user or not user.is_active:
        session.clear()
        return None
    return user


def login_required(f):
    """Decorator requiring active authenticated user."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login', next=request.path))
        user = get_current_user()
        if not user:
            flash('Your account has been deactivated or not found. Please log in again.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def candidate_required(f):
    """Decorator requiring active user with 'candidate' role."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in as a Candidate to access this page.', 'warning')
            return redirect(url_for('auth.login', next=request.path))
        user = get_current_user()
        if not user or user.role != 'candidate':
            flash('Access restricted: Candidate account required.', 'danger')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function


def employer_required(f):
    """Decorator requiring active user with 'employer' role."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in as an Employer to access this page.', 'warning')
            return redirect(url_for('auth.login', next=request.path))
        user = get_current_user()
        if not user or user.role != 'employer':
            flash('Access restricted: Employer account required.', 'danger')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorator requiring active user with 'admin' role."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Administrator authentication required.', 'warning')
            return redirect(url_for('auth.login', next=request.path))
        user = get_current_user()
        if not user or user.role != 'admin':
            flash('Access denied: Administrator privileges required.', 'danger')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function


def register_user(name, email, password, role, phone=None, location=None, company_name=None):
    """Register a new user and create their respective candidate or company profile."""
    email = email.strip().lower()
    if User.query.filter_by(email=email).first():
        return None, 'An account with this email address already exists.'

    if role not in ['candidate', 'employer']:
        return None, 'Invalid account role specified.'

    user = User(
        name=name.strip(),
        email=email,
        role=role,
        phone=phone.strip() if phone else None,
        location=location.strip() if location else None,
        is_active=True
    )
    user.set_password(password)
    db.session.add(user)
    db.session.flush()  # generates user.id

    if role == 'candidate':
        profile = CandidateProfile(user_id=user.id)
        db.session.add(profile)
    elif role == 'employer':
        c_name = company_name.strip() if company_name else f"{user.name}'s Company"
        company = Company(
            user_id=user.id,
            company_name=c_name,
            location=user.location
        )
        db.session.add(company)

    db.session.commit()

    # Dispatch notifications
    from services.notification_service import create_notification, notify_admin
    if role == 'candidate':
        create_notification(
            user.id,
            "Welcome to JobPortal!",
            "Your candidate account has been created. Start by updating your profile and uploading your resume.",
            link="/candidate/profile"
        )
        notify_admin(
            "New Candidate Registered",
            f"{user.name} ({user.email}) registered as a Job Seeker.",
            link="/admin/users"
        )
    elif role == 'employer':
        create_notification(
            user.id,
            "Welcome to JobPortal!",
            "Your employer account has been created. Complete your company profile to start posting roles.",
            link="/employer/company-profile"
        )
        notify_admin(
            "New Employer Registered",
            f"{user.name} ({user.email}) registered with company '{company_name}'.",
            link="/admin/employers"
        )

    return user, None
