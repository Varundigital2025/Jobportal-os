from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, jsonify, send_from_directory
from extensions import db
from models.user import User
from models.candidate import CandidateProfile
from models.company import Company
from models.job import Job
from models.application import Application
from models.system_setting import SystemSetting
from services.auth_service import get_current_user, admin_required
from services.application_service import update_application_status
from services.file_service import save_resume, save_profile_photo, save_company_logo, save_branding_image
from services.settings_service import (
    get_all_settings, get_setting, set_setting, update_settings, generate_secure_api_key,
    THEME_PRESETS, normalize_hex_color, resolve_theme_color, generate_theme_palette
)
from routes.jobs import CATEGORIES, JOB_TYPES, WORK_MODES, EXPERIENCE_LEVELS
from config import Config

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

APPLICATION_STATUSES = ['Applied', 'Under Review', 'Shortlisted', 'Interview', 'Rejected', 'Selected']


@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    total_users = User.query.count()
    candidate_count = User.query.filter_by(role='candidate').count()
    employer_count = User.query.filter_by(role='employer').count()
    total_jobs = Job.query.count()
    active_jobs = Job.query.filter_by(status='Open').count()
    total_applications = Application.query.count()

    # Application status counts for analytics chart
    status_counts = {}
    for status in APPLICATION_STATUSES:
        status_counts[status] = Application.query.filter_by(status=status).count()

    # Category distribution for analytics chart
    from sqlalchemy import func
    category_counts = db.session.query(
        Job.category, func.count(Job.id)
    ).group_by(Job.category).limit(6).all()
    category_labels = [c[0] for c in category_counts]
    category_data = [c[1] for c in category_counts]

    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    recent_jobs = Job.query.order_by(Job.created_at.desc()).limit(5).all()
    recent_apps = Application.query.order_by(Application.applied_at.desc()).limit(5).all()

    return render_template(
        'admin/dashboard.html',
        total_users=total_users,
        candidate_count=candidate_count,
        employer_count=employer_count,
        total_jobs=total_jobs,
        active_jobs=active_jobs,
        total_applications=total_applications,
        status_labels=list(status_counts.keys()),
        status_data=list(status_counts.values()),
        category_labels=category_labels,
        category_data=category_data,
        recent_users=recent_users,
        recent_jobs=recent_jobs,
        recent_apps=recent_apps
    )


@admin_bp.route('/users')
@admin_required
def users():
    q = request.args.get('q', '').strip()
    role_filter = request.args.get('role', '').strip()
    page = request.args.get('page', 1, type=int)

    query = User.query
    if q:
        term = f"%{q}%"
        query = query.filter((User.name.ilike(term)) | (User.email.ilike(term)))
    if role_filter and role_filter != 'All':
        query = query.filter_by(role=role_filter)

    pagination = query.order_by(User.created_at.desc()).paginate(page=page, per_page=15, error_out=False)

    return render_template(
        'admin/users.html',
        pagination=pagination,
        users=pagination.items,
        search_query=q,
        selected_role=role_filter
    )


@admin_bp.route('/users/create', methods=['GET', 'POST'])
@admin_required
def create_user():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '').strip()
        role = request.form.get('role', 'candidate').strip().lower()
        phone = request.form.get('phone', '').strip()
        location = request.form.get('location', '').strip()
        is_active = request.form.get('is_active', '1') == '1'

        # Validation
        if not name or not email or not password:
            flash('Full Name, Email Address, and Password are required fields.', 'danger')
            return render_template('admin/create-user.html', form_data=request.form)

        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return render_template('admin/create-user.html', form_data=request.form)

        if role not in ['candidate', 'employer', 'admin']:
            flash('Invalid account role selected.', 'danger')
            return render_template('admin/create-user.html', form_data=request.form)

        if User.query.filter_by(email=email).first():
            flash(f'An account with email "{email}" already exists. Please use a unique email address.', 'danger')
            return render_template('admin/create-user.html', form_data=request.form)

        # Create user instance
        user = User(
            name=name,
            email=email,
            role=role,
            phone=phone if phone else None,
            location=location if location else None,
            is_active=is_active
        )
        user.set_password(password)

        # Profile photo upload if provided
        photo_file = request.files.get('profile_photo')
        if photo_file and photo_file.filename and photo_file.filename.strip():
            photo_fn, photo_err = save_profile_photo(photo_file)
            if not photo_err:
                user.profile_photo = photo_fn
            else:
                flash(f"Profile photo warning: {photo_err}", 'warning')

        db.session.add(user)
        db.session.flush()  # generates user.id

        # Role-specific profile initialization
        if role == 'candidate':
            headline = request.form.get('headline', '').strip()
            bio = request.form.get('bio', '').strip()
            skills = request.form.get('skills', '').strip()
            experience = request.form.get('experience', '').strip()
            education = request.form.get('education', '').strip()
            qualification = request.form.get('qualification', '').strip()
            linkedin_url = request.form.get('linkedin_url', '').strip()
            portfolio_url = request.form.get('portfolio_url', '').strip()

            c_profile = CandidateProfile(
                user_id=user.id,
                headline=headline if headline else None,
                bio=bio if bio else None,
                skills=skills if skills else None,
                experience=experience if experience else None,
                education=education if education else None,
                qualification=qualification if qualification else None,
                linkedin_url=linkedin_url if linkedin_url else None,
                portfolio_url=portfolio_url if portfolio_url else None
            )

            # Resume upload if provided
            resume_file = request.files.get('resume')
            if resume_file and resume_file.filename and resume_file.filename.strip():
                resume_fn, res_err = save_resume(resume_file)
                if not res_err:
                    c_profile.resume_path = resume_fn
                    clean_name = resume_file.filename.replace('\\', '/').split('/')[-1].strip()
                    c_profile.resume_filename = clean_name or f"resume_{user.id}.pdf"
                else:
                    flash(f"Resume upload warning: {res_err}", 'warning')

            db.session.add(c_profile)

        elif role == 'employer':
            company_name = request.form.get('company_name', '').strip() or f"{user.name}'s Company"
            industry = request.form.get('industry', 'Software & Engineering').strip()
            company_size = request.form.get('company_size', '11-50').strip()
            website = request.form.get('website', '').strip()
            description = request.form.get('company_description', '').strip()

            comp = Company(
                user_id=user.id,
                company_name=company_name,
                industry=industry,
                company_size=company_size,
                website=website if website else None,
                description=description if description else None,
                location=user.location
            )

            # Company logo if provided
            logo_file = request.files.get('company_logo')
            if logo_file and logo_file.filename and logo_file.filename.strip():
                logo_fn, logo_err = save_company_logo(logo_file)
                if not logo_err:
                    comp.logo = logo_fn
                else:
                    flash(f"Company logo warning: {logo_err}", 'warning')

            db.session.add(comp)

        db.session.commit()

        # Send welcome notification
        from services.notification_service import create_notification
        welcome_link = "/candidate/profile" if role == 'candidate' else ("/employer/company-profile" if role == 'employer' else "/admin/dashboard")
        create_notification(
            user.id,
            "Account Created by Administrator",
            f"Your {role.title()} account has been created by the platform administrator. You can now log in with your credentials.",
            link=welcome_link
        )

        flash(f'New {role.title()} account "{user.name}" ({user.email}) has been created successfully and saved in the database!', 'success')
        return redirect(url_for('admin.users'))

    return render_template('admin/create-user.html', form_data={})


@admin_bp.route('/users/<int:user_id>/toggle-status', methods=['POST'])
@admin_required
def toggle_user_status(user_id):
    current_admin = get_current_user()
    if user_id == current_admin.id:
        flash('You cannot deactivate your own administrative account.', 'warning')
        return redirect(url_for('admin.users'))

    user = db.session.get(User, user_id)
    if not user:
        abort(404)

    user.is_active = not user.is_active
    db.session.commit()

    state = "activated" if user.is_active else "deactivated"
    flash(f'User "{user.name}" has been {state}.', 'success')
    return redirect(request.referrer or url_for('admin.users'))


@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@admin_required
def delete_user(user_id):
    current_admin = get_current_user()
    if user_id == current_admin.id:
        flash('You cannot delete your own active administrator account.', 'danger')
        return redirect(url_for('admin.users'))

    # Prevent deleting the last admin
    user = db.session.get(User, user_id)
    if not user:
        abort(404)

    if user.role == 'admin':
        admin_count = User.query.filter_by(role='admin').count()
        if admin_count <= 1:
            flash('Cannot delete the last remaining administrator account.', 'danger')
            return redirect(url_for('admin.users'))

    db.session.delete(user)
    db.session.commit()
    flash(f'User "{user.name}" and associated records have been removed.', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/employers')
@admin_required
def employers():
    q = request.args.get('q', '').strip()
    query = Company.query
    if q:
        term = f"%{q}%"
        query = query.filter(Company.company_name.ilike(term))

    companies = query.order_by(Company.created_at.desc()).all()
    return render_template('admin/employers.html', companies=companies, search_query=q)


@admin_bp.route('/jobs')
@admin_required
def jobs():
    q = request.args.get('q', '').strip()
    status_filter = request.args.get('status', '').strip()
    category_filter = request.args.get('category', '').strip()
    page = request.args.get('page', 1, type=int)

    query = Job.query
    if q:
        term = f"%{q}%"
        query = query.filter(Job.title.ilike(term))
    if status_filter and status_filter != 'All':
        query = query.filter_by(status=status_filter)
    if category_filter and category_filter != 'All':
        query = query.filter_by(category=category_filter)

    pagination = query.order_by(Job.created_at.desc()).paginate(page=page, per_page=15, error_out=False)

    return render_template(
        'admin/jobs.html',
        pagination=pagination,
        jobs=pagination.items,
        search_query=q,
        selected_status=status_filter,
        selected_category=category_filter
    )


@admin_bp.route('/jobs/create', methods=['GET', 'POST'])
@admin_required
def create_job():
    companies = Company.query.order_by(Company.company_name.asc()).all()
    current_admin = get_current_user()

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        company_id = request.form.get('company_id', type=int)
        category = request.form.get('category', '').strip()
        description = request.form.get('description', '').strip()
        responsibilities = request.form.get('responsibilities', '').strip()
        requirements = request.form.get('requirements', '').strip()
        skills = request.form.get('skills', '').strip()
        location = request.form.get('location', '').strip()
        job_type = request.form.get('job_type', 'Full Time').strip()
        work_mode = request.form.get('work_mode', 'On-site').strip()
        experience_level = request.form.get('experience_level', 'Mid Level').strip()
        salary_currency = request.form.get('salary_currency', '').strip()
        if not salary_currency:
            from services.currency_service import detect_currency_from_location
            detected = detect_currency_from_location(location)
            salary_currency = detected['symbol'] if detected else '₹'
        status = request.form.get('status', 'Open').strip()

        # Parse salary
        salary_min = None
        salary_max = None
        if request.form.get('salary_min'):
            try:
                salary_min = int(request.form.get('salary_min'))
            except ValueError:
                pass
        if request.form.get('salary_max'):
            try:
                salary_max = int(request.form.get('salary_max'))
            except ValueError:
                pass

        # Parse deadline
        deadline = None
        deadline_str = request.form.get('deadline', '').strip()
        if deadline_str:
            try:
                deadline = datetime.strptime(deadline_str, '%Y-%m-%d').date()
            except ValueError:
                pass

        if not title or not category or not description or not location:
            flash('Please complete all mandatory fields: Job Title, Category, Location, and Description.', 'danger')
            return render_template(
                'admin/create-job.html',
                companies=companies,
                form_data=request.form,
                categories=CATEGORIES,
                job_types=JOB_TYPES,
                work_modes=WORK_MODES,
                experience_levels=EXPERIENCE_LEVELS
            )

        # Company & Employer resolution
        selected_company = db.session.get(Company, company_id) if company_id else None
        if selected_company:
            employer_id = selected_company.user_id
            comp_id = selected_company.id
        else:
            # Default to admin's platform company
            admin_company = current_admin.company
            if not admin_company:
                admin_company = Company(
                    user_id=current_admin.id,
                    company_name="JobPortal Administration",
                    industry="Technology & Platform",
                    location=current_admin.location or "Global / Remote",
                    description="Official roles verified and posted directly by JobPortal administrators."
                )
                db.session.add(admin_company)
                db.session.commit()
            employer_id = current_admin.id
            comp_id = admin_company.id

        job = Job(
            employer_id=employer_id,
            company_id=comp_id,
            title=title,
            category=category,
            description=description,
            responsibilities=responsibilities,
            requirements=requirements,
            skills=skills,
            location=location,
            job_type=job_type,
            work_mode=work_mode,
            experience_level=experience_level,
            salary_min=salary_min,
            salary_max=salary_max,
            salary_currency=salary_currency,
            deadline=deadline,
            status=status
        )
        db.session.add(job)
        db.session.commit()

        flash(f'Job "{job.title}" posted successfully by Admin and is now live on the website!', 'success')
        return redirect(url_for('admin.jobs'))

    return render_template(
        'admin/create-job.html',
        companies=companies,
        form_data={},
        categories=CATEGORIES,
        job_types=JOB_TYPES,
        work_modes=WORK_MODES,
        experience_levels=EXPERIENCE_LEVELS
    )


@admin_bp.route('/jobs/<int:job_id>/status', methods=['POST'])
@admin_required
def change_job_status(job_id):
    job = db.session.get(Job, job_id)
    if not job:
        abort(404)

    new_status = request.form.get('status')
    if new_status in ['Open', 'Closed', 'Draft']:
        job.status = new_status
        db.session.commit()
        flash(f'Job "{job.title}" status changed to {new_status}.', 'success')

    return redirect(request.referrer or url_for('admin.jobs'))


@admin_bp.route('/jobs/<int:job_id>/delete', methods=['POST'])
@admin_required
def delete_job(job_id):
    job = db.session.get(Job, job_id)
    if not job:
        abort(404)

    db.session.delete(job)
    db.session.commit()
    flash(f'Job "{job.title}" deleted by administrator.', 'success')
    return redirect(request.referrer or url_for('admin.jobs'))


@admin_bp.route('/applications')
@admin_required
def applications():
    status_filter = request.args.get('status', '').strip()
    page = request.args.get('page', 1, type=int)

    query = Application.query
    if status_filter and status_filter != 'All':
        query = query.filter_by(status=status_filter)

    pagination = query.order_by(Application.applied_at.desc()).paginate(page=page, per_page=15, error_out=False)

    return render_template(
        'admin/applications.html',
        pagination=pagination,
        applications=pagination.items,
        selected_status=status_filter,
        statuses=APPLICATION_STATUSES
    )


@admin_bp.route('/applications/<int:app_id>/status', methods=['POST'])
@admin_required
def update_application_status_route(app_id):
    current_admin = get_current_user()
    new_status = request.form.get('status', '').strip()
    admin_notes = request.form.get('admin_notes', '').strip()
    success, msg = update_application_status(app_id, new_status, current_admin, admin_notes=admin_notes)

    if success:
        flash(f"Application #{app_id} status updated to '{new_status}'. The candidate has been notified and can see the update live on their dashboard.", 'success')
    else:
        flash(msg, 'danger')

    return redirect(request.referrer or url_for('admin.applications'))


@admin_bp.route('/applications/<int:app_id>/resume')
@admin_required
def download_resume(app_id):
    application = db.session.get(Application, app_id)
    if not application:
        abort(404)

    if not application.resume_path:
        flash('Candidate has not attached a resume.', 'warning')
        return redirect(url_for('admin.applications'))

    download_filename = f"Resume_{application.candidate.name.replace(' ', '_')}.pdf"
    return send_from_directory(
        Config.RESUME_FOLDER,
        application.resume_path,
        as_attachment=True,
        download_name=download_filename
    )


@admin_bp.route('/settings', methods=['GET', 'POST'])
@admin_required
def settings():
    current_admin = get_current_user()
    active_tab = request.args.get('tab', 'admin_portal').strip()

    if request.method == 'POST':
        action = request.form.get('action', '').strip()

        # 1. Update Admin Portal Branding & Details
        if action == 'update_admin_branding':
            admin_portal_name = request.form.get('admin_portal_name', '').strip()
            admin_portal_tagline = request.form.get('admin_portal_tagline', '').strip()
            admin_badge_text = request.form.get('admin_badge_text', '').strip()
            admin_theme = request.form.get('admin_theme', '').strip()
            theme_color = request.form.get('theme_color', '').strip()

            if not admin_portal_name:
                flash('Admin Portal Name cannot be empty.', 'danger')
                return redirect(url_for('admin.settings', tab='admin_portal'))

            # Resolve color and theme preset
            if theme_color:
                resolved_hex = normalize_hex_color(theme_color)
            elif admin_theme:
                resolved_hex = resolve_theme_color(admin_theme)
            else:
                resolved_hex = '#2563EB'

            # Check if resolved hex matches any preset
            resolved_preset_key = None
            for k, v in THEME_PRESETS.items():
                if v['primary'].upper() == resolved_hex.upper():
                    resolved_preset_key = k
                    break

            # If user explicitly picked a preset name and didn't provide a different custom hex
            if admin_theme.lower() in THEME_PRESETS and (not theme_color or THEME_PRESETS[admin_theme.lower()]['primary'].upper() == resolved_hex.upper()):
                final_admin_theme = admin_theme.lower()
            elif resolved_preset_key:
                final_admin_theme = resolved_preset_key
            else:
                final_admin_theme = resolved_hex

            updates = {
                'admin_portal_name': admin_portal_name,
                'admin_portal_tagline': admin_portal_tagline,
                'admin_badge_text': admin_badge_text or 'SuperAdmin Console',
                'admin_theme': final_admin_theme,
                'theme_color': resolved_hex,
            }

            # Check if admin logo was uploaded
            logo_file = request.files.get('admin_portal_logo')
            sync_site = request.form.get('sync_site_logo', '1') in ['1', 'true', 'on']
            if logo_file and logo_file.filename and logo_file.filename.strip():
                logo_fn, err = save_branding_image(logo_file, prefix='admin_logo_')
                if err:
                    flash(f'Admin portal logo error: {err}', 'danger')
                    return redirect(url_for('admin.settings', tab='admin_portal'))
                updates['admin_portal_logo'] = logo_fn
                if sync_site:
                    updates['site_logo'] = logo_fn

            update_settings(updates)
            flash('Admin Portal branding, logo, and console details updated successfully!', 'success')
            return redirect(url_for('admin.settings', tab='admin_portal'))

        # 2. Remove Admin Portal Logo
        elif action == 'remove_admin_logo':
            set_setting('admin_portal_logo', '', group='admin_portal')
            flash('Custom Admin Portal logo removed. Default portal iconography restored.', 'info')
            return redirect(url_for('admin.settings', tab='admin_portal'))

        # 3. Update Website Details & Public Logo
        elif action == 'update_site_branding':
            site_name = request.form.get('site_name', '').strip()
            site_tagline = request.form.get('site_tagline', '').strip()
            contact_email = request.form.get('contact_email', '').strip()
            contact_phone = request.form.get('contact_phone', '').strip()
            company_address = request.form.get('company_address', '').strip()
            footer_text = request.form.get('footer_text', '').strip()
            copyright_text = request.form.get('copyright_text', '').strip()
            social_linkedin = request.form.get('social_linkedin', '').strip()
            social_github = request.form.get('social_github', '').strip()
            social_twitter = request.form.get('social_twitter', '').strip()

            if not site_name:
                flash('Website Name cannot be empty.', 'danger')
                return redirect(url_for('admin.settings', tab='website'))

            updates = {
                'site_name': site_name,
                'site_tagline': site_tagline,
                'contact_email': contact_email,
                'contact_phone': contact_phone,
                'company_address': company_address,
                'footer_text': footer_text,
                'copyright_text': copyright_text,
                'social_linkedin': social_linkedin,
                'social_github': social_github,
                'social_twitter': social_twitter,
            }

            # Check website logo upload
            site_logo_file = request.files.get('site_logo')
            sync_admin = request.form.get('sync_admin_logo', '1') in ['1', 'true', 'on']
            if site_logo_file and site_logo_file.filename and site_logo_file.filename.strip():
                logo_fn, err = save_branding_image(site_logo_file, prefix='site_logo_')
                if err:
                    flash(f'Website logo error: {err}', 'danger')
                    return redirect(url_for('admin.settings', tab='website'))
                updates['site_logo'] = logo_fn
                if sync_admin:
                    updates['admin_portal_logo'] = logo_fn

            # Check favicon upload
            favicon_file = request.files.get('site_favicon')
            if favicon_file and favicon_file.filename and favicon_file.filename.strip():
                fav_fn, err = save_branding_image(favicon_file, prefix='favicon_')
                if not err:
                    updates['site_favicon'] = fav_fn

            update_settings(updates)
            flash('Public website branding, logo, and contact details updated successfully!', 'success')
            return redirect(url_for('admin.settings', tab='website'))

        # 4. Remove Website Logo
        elif action == 'remove_site_logo':
            set_setting('site_logo', '', group='general')
            flash('Custom website logo removed. Standard website icon is restored.', 'info')
            return redirect(url_for('admin.settings', tab='website'))

        # 5. Update Integrations & Platform Controls
        elif action == 'update_integrations':
            webhook_url = request.form.get('webhook_url', '').strip()
            webhook_secret = request.form.get('webhook_secret', '').strip()
            api_key = request.form.get('api_key', '').strip()
            integration_mode = request.form.get('integration_mode', 'standalone').strip()
            allow_cand = 'true' if request.form.get('allow_candidate_registration') == '1' else 'false'
            allow_emp = 'true' if request.form.get('allow_employer_registration') == '1' else 'false'
            maint_mode = 'true' if request.form.get('maintenance_mode') == '1' else 'false'
            custom_css = request.form.get('custom_css', '').strip()
            custom_header_script = request.form.get('custom_header_script', '').strip()

            updates = {
                'webhook_url': webhook_url,
                'webhook_secret': webhook_secret,
                'api_key': api_key,
                'integration_mode': integration_mode,
                'allow_candidate_registration': allow_cand,
                'allow_employer_registration': allow_emp,
                'maintenance_mode': maint_mode,
                'custom_css': custom_css,
                'custom_header_script': custom_header_script
            }
            update_settings(updates)
            flash('Integration endpoints and platform controls saved successfully!', 'success')
            return redirect(url_for('admin.settings', tab='integrations'))

        # 6. Generate API Key
        elif action == 'generate_api_key':
            new_key = generate_secure_api_key()
            set_setting('api_key', new_key, group='integration')
            flash(f'New Integration API Key generated: {new_key}', 'success')
            return redirect(url_for('admin.settings', tab='integrations'))

        # 7. Change Admin Password
        elif action == 'change_password':
            current_password = request.form.get('current_password', '')
            new_password = request.form.get('new_password', '')
            confirm_password = request.form.get('confirm_password', '')

            if not current_password or not new_password or not confirm_password:
                flash('All password fields are required.', 'danger')
                return redirect(url_for('admin.settings', tab='security'))

            if not current_admin.check_password(current_password):
                flash('Current administrator password is incorrect.', 'danger')
                return redirect(url_for('admin.settings', tab='security'))

            if len(new_password) < 6:
                flash('New administrator password must be at least 6 characters long.', 'danger')
                return redirect(url_for('admin.settings', tab='security'))

            if new_password != confirm_password:
                flash('New password and confirmation password do not match.', 'danger')
                return redirect(url_for('admin.settings', tab='security'))

            current_admin.set_password(new_password)
            db.session.commit()

            # Record security notification
            from services.notification_service import create_notification
            create_notification(
                current_admin.id,
                "Security Alert: Admin Password Updated",
                "Your administrator account password was changed from Admin Portal Settings.",
                link="/admin/settings?tab=security"
            )

            flash('Administrator password updated successfully! Please keep your credentials secure.', 'success')
            return redirect(url_for('admin.settings', tab='security'))

        # 8. Update Admin Profile
        elif action == 'update_admin_profile':
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip().lower()
            phone = request.form.get('phone', '').strip()
            location = request.form.get('location', '').strip()

            if not name or not email:
                flash('Administrator Name and Email are required.', 'danger')
                return redirect(url_for('admin.settings', tab='security'))

            # Check if email taken by another user
            existing = User.query.filter(User.email == email, User.id != current_admin.id).first()
            if existing:
                flash(f'The email "{email}" is already used by another account.', 'danger')
                return redirect(url_for('admin.settings', tab='security'))

            current_admin.name = name
            current_admin.email = email
            current_admin.phone = phone if phone else None
            current_admin.location = location if location else None

            photo_file = request.files.get('profile_photo')
            if photo_file and photo_file.filename and photo_file.filename.strip():
                photo_fn, err = save_profile_photo(photo_file)
                if not err:
                    current_admin.profile_photo = photo_fn
                else:
                    flash(f'Profile photo warning: {err}', 'warning')

            db.session.commit()
            flash('Administrator profile information saved successfully.', 'success')
            return redirect(url_for('admin.settings', tab='security'))

        else:
            flash('Unrecognized settings action.', 'warning')
            return redirect(url_for('admin.settings'))

    settings_data = get_all_settings()
    return render_template(
        'admin/settings.html',
        settings=settings_data,
        current_admin=current_admin,
        active_tab=active_tab
    )


@admin_bp.route('/api/portal-info')
def api_portal_info():
    """
    Public / Integration status endpoint providing portal details and health.
    Can be queried by external ERPs or monitoring microservices.
    """
    settings_data = get_all_settings()
    return jsonify({
        'status': 'healthy',
        'site_name': settings_data.get('site_name'),
        'admin_portal_name': settings_data.get('admin_portal_name'),
        'integration_mode': settings_data.get('integration_mode'),
        'timestamp': datetime.utcnow().isoformat()
    })


@admin_bp.route('/api/upload-logo', methods=['POST'])
@admin_required
def upload_logo_ajax():
    """
    Instant AJAX logo upload endpoint. Saves the branding logo immediately
    and updates both admin and website logo records so it never disappears on reload.
    """
    target = request.form.get('target', 'both')  # 'admin', 'site', 'both'
    logo_file = request.files.get('logo') or request.files.get('admin_portal_logo') or request.files.get('site_logo')
    if not logo_file or not logo_file.filename or not logo_file.filename.strip():
        return jsonify({'success': False, 'error': 'No image file was provided.'}), 400

    prefix = 'admin_logo_' if target == 'admin' else ('site_logo_' if target == 'site' else 'brand_logo_')
    saved_fn, err = save_branding_image(logo_file, prefix=prefix)
    if err:
        return jsonify({'success': False, 'error': err}), 400

    updates = {}
    if target in ['admin', 'both']:
        updates['admin_portal_logo'] = saved_fn
    if target in ['site', 'both']:
        updates['site_logo'] = saved_fn

    update_settings(updates)
    logo_url = url_for('serve_branding_logo', filename=saved_fn)
    return jsonify({
        'success': True,
        'filename': saved_fn,
        'url': logo_url,
        'message': 'Logo uploaded and saved successfully across all pages!'
    })


