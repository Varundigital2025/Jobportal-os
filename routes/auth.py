from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from extensions import db
from models.user import User
from services.auth_service import register_user, login_user, logout_user, get_current_user

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if session.get('user_id'):
        user = get_current_user()
        if user:
            if user.role == 'candidate':
                return redirect(url_for('candidate.dashboard'))
            elif user.role == 'employer':
                return redirect(url_for('employer.dashboard'))
            elif user.role == 'admin':
                return redirect(url_for('admin.dashboard'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        phone = request.form.get('phone', '').strip()
        location = request.form.get('location', '').strip()
        role = 'candidate'  # Public registration is strictly for job seekers / candidates

        # Validation
        if not name or not email or not password:
            flash('Please fill in all required fields (Name, Email, and Password).', 'danger')
            return render_template('auth/register.html', form_data=request.form)

        if '@' not in email or '.' not in email:
            flash('Please enter a valid email address.', 'danger')
            return render_template('auth/register.html', form_data=request.form)

        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return render_template('auth/register.html', form_data=request.form)

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/register.html', form_data=request.form)

        user, err = register_user(
            name=name,
            email=email,
            password=password,
            role=role,
            phone=phone,
            location=location
        )

        if err:
            flash(err, 'danger')
            return render_template('auth/register.html', form_data=request.form)

        # Automatically log the user in upon successful registration
        login_user(user)
        flash(f'Account created successfully! Welcome to JobPortal, {user.name}.', 'success')
        return redirect(url_for('candidate.dashboard'))

    # Initial GET view
    return render_template('auth/register.html', form_data={})


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('user_id'):
        user = get_current_user()
        if user:
            if user.role == 'candidate':
                return redirect(url_for('candidate.dashboard'))
            elif user.role == 'employer':
                return redirect(url_for('employer.dashboard'))
            elif user.role == 'admin':
                return redirect(url_for('admin.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember'))

        if not email or not password:
            flash('Please enter both email and password.', 'warning')
            return render_template('auth/login.html')

        user = User.query.filter_by(email=email).first()

        if not user or not user.check_password(password):
            flash('Invalid email or password. Please try again.', 'danger')
            return render_template('auth/login.html', email=email)

        if not user.is_active:
            flash('Your account has been deactivated by administrator. Please contact support.', 'danger')
            return render_template('auth/login.html')

        login_user(user, remember=remember)
        flash(f'Welcome back, {user.name}!', 'success')

        next_page = request.args.get('next')
        if next_page and next_page.startswith('/'):
            return redirect(next_page)

        if user.role == 'candidate':
            return redirect(url_for('candidate.dashboard'))
        elif user.role == 'employer':
            return redirect(url_for('employer.dashboard'))
        elif user.role == 'admin':
            return redirect(url_for('admin.dashboard'))

        return redirect(url_for('home'))

    return render_template('auth/login.html')


@auth_bp.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('home'))


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        user = User.query.filter_by(email=email).first()
        if user:
            flash('If an account exists with that email, password reset instructions have been dispatched.', 'success')
        else:
            flash('If an account exists with that email, password reset instructions have been dispatched.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/forgot-password.html')
