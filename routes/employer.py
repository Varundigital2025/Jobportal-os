import os
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_from_directory, abort
from extensions import db
from models.user import User
from models.company import Company
from models.job import Job
from models.application import Application
from services.auth_service import get_current_user, employer_required
from services.file_service import save_company_logo
from services.application_service import update_application_status
from config import Config

employer_bp = Blueprint('employer', __name__, url_prefix='/employer')

JOB_TYPES = ['Full Time', 'Part Time', 'Contract', 'Internship', 'Freelance']
WORK_MODES = ['On-site', 'Remote', 'Hybrid']
EXPERIENCE_LEVELS = ['Entry Level', 'Mid Level', 'Senior Level', 'Lead / Manager', 'Executive']
CATEGORIES = [
    'Software & Engineering',
    'Data Science & AI',
    'Product & Design',
    'Marketing & Content',
    'Sales & Business Development',
    'Finance & Accounting',
    'Customer Success & Support',
    'Human Resources',
    'Healthcare & Science',
    'Operations & Logistics'
]
APPLICATION_STATUSES = ['Applied', 'Under Review', 'Shortlisted', 'Interview', 'Rejected', 'Selected']


def get_or_create_company(user):
    company = user.company
    if not company:
        company = Company(
            user_id=user.id,
            company_name=f"{user.name}'s Company",
            location=user.location
        )
        db.session.add(company)
        db.session.commit()
    return company


@employer_bp.route('/dashboard')
@employer_required
def dashboard():
    user = get_current_user()
    company = get_or_create_company(user)

    jobs = Job.query.filter_by(employer_id=user.id).order_by(Job.created_at.desc()).all()
    total_jobs = len(jobs)
    active_jobs = sum(1 for j in jobs if j.status == 'Open')

    # Applications across all this employer's jobs
    job_ids = [j.id for j in jobs]
    if job_ids:
        all_apps = Application.query.filter(Application.job_id.in_(job_ids)).all()
    else:
        all_apps = []

    total_applications = len(all_apps)
    new_applications = sum(1 for a in all_apps if a.status == 'Applied')
    shortlisted_candidates = sum(1 for a in all_apps if a.status in ['Shortlisted', 'Interview', 'Selected'])

    # Recent 5 jobs
    recent_jobs = jobs[:5]

    return render_template(
        'employer/dashboard.html',
        user=user,
        company=company,
        total_jobs=total_jobs,
        active_jobs=active_jobs,
        total_applications=total_applications,
        new_applications=new_applications,
        shortlisted_candidates=shortlisted_candidates,
        recent_jobs=recent_jobs
    )


@employer_bp.route('/company-profile', methods=['GET', 'POST'])
@employer_required
def company_profile():
    user = get_current_user()
    company = get_or_create_company(user)

    if request.method == 'POST':
        company.company_name = request.form.get('company_name', company.company_name).strip()
        company.industry = request.form.get('industry', '').strip()
        company.company_size = request.form.get('company_size', '').strip()
        company.website = request.form.get('website', '').strip()
        company.location = request.form.get('location', '').strip()
        company.phone = request.form.get('phone', '').strip()
        company.description = request.form.get('description', '').strip()

        logo_file = request.files.get('logo')
        if logo_file and logo_file.filename:
            filename, err = save_company_logo(logo_file)
            if err:
                flash(err, 'danger')
            else:
                company.logo = filename

        db.session.commit()
        flash('Company profile updated successfully!', 'success')
        return redirect(url_for('employer.company_profile'))

    return render_template('employer/company-profile.html', user=user, company=company)


@employer_bp.route('/jobs')
@employer_required
def manage_jobs():
    user = get_current_user()
    status_filter = request.args.get('status', '').strip()

    query = Job.query.filter_by(employer_id=user.id)
    if status_filter and status_filter != 'All':
        query = query.filter_by(status=status_filter)

    jobs = query.order_by(Job.created_at.desc()).all()
    return render_template('employer/jobs.html', jobs=jobs, selected_status=status_filter)


@employer_bp.route('/jobs/create', methods=['GET', 'POST'])
@employer_required
def create_job():
    user = get_current_user()
    company = get_or_create_company(user)

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        category = request.form.get('category', '').strip()
        description = request.form.get('description', '').strip()
        responsibilities = request.form.get('responsibilities', '').strip()
        requirements = request.form.get('requirements', '').strip()
        skills = request.form.get('skills', '').strip()
        location = request.form.get('location', '').strip()
        job_type = request.form.get('job_type', 'Full Time').strip()
        work_mode = request.form.get('work_mode', 'On-site').strip()
        experience_level = request.form.get('experience_level', 'Mid Level').strip()
        salary_currency = request.form.get('salary_currency', '$').strip()
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
                'employer/create-job.html',
                form_data=request.form,
                categories=CATEGORIES,
                job_types=JOB_TYPES,
                work_modes=WORK_MODES,
                experience_levels=EXPERIENCE_LEVELS
            )

        job = Job(
            employer_id=user.id,
            company_id=company.id,
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

        flash(f'Job "{job.title}" posted successfully!', 'success')
        return redirect(url_for('employer.manage_jobs'))

    return render_template(
        'employer/create-job.html',
        form_data={},
        categories=CATEGORIES,
        job_types=JOB_TYPES,
        work_modes=WORK_MODES,
        experience_levels=EXPERIENCE_LEVELS
    )


@employer_bp.route('/jobs/<int:job_id>/edit', methods=['GET', 'POST'])
@employer_required
def edit_job(job_id):
    user = get_current_user()
    job = db.session.get(Job, job_id)
    if not job:
        abort(404)

    # Security: employer A cannot modify employer B's jobs
    if job.employer_id != user.id:
        abort(403)

    if request.method == 'POST':
        job.title = request.form.get('title', job.title).strip()
        job.category = request.form.get('category', job.category).strip()
        job.description = request.form.get('description', job.description).strip()
        job.responsibilities = request.form.get('responsibilities', '').strip()
        job.requirements = request.form.get('requirements', '').strip()
        job.skills = request.form.get('skills', '').strip()
        job.location = request.form.get('location', job.location).strip()
        job.job_type = request.form.get('job_type', job.job_type).strip()
        job.work_mode = request.form.get('work_mode', job.work_mode).strip()
        job.experience_level = request.form.get('experience_level', job.experience_level).strip()
        job.salary_currency = request.form.get('salary_currency', '$').strip()
        job.status = request.form.get('status', job.status).strip()

        # Parse salary
        if request.form.get('salary_min'):
            try:
                job.salary_min = int(request.form.get('salary_min'))
            except ValueError:
                job.salary_min = None
        else:
            job.salary_min = None

        if request.form.get('salary_max'):
            try:
                job.salary_max = int(request.form.get('salary_max'))
            except ValueError:
                job.salary_max = None
        else:
            job.salary_max = None

        # Parse deadline
        deadline_str = request.form.get('deadline', '').strip()
        if deadline_str:
            try:
                job.deadline = datetime.strptime(deadline_str, '%Y-%m-%d').date()
            except ValueError:
                job.deadline = None
        else:
            job.deadline = None

        db.session.commit()
        flash(f'Job "{job.title}" updated successfully!', 'success')
        return redirect(url_for('employer.manage_jobs'))

    return render_template(
        'employer/edit-job.html',
        job=job,
        categories=CATEGORIES,
        job_types=JOB_TYPES,
        work_modes=WORK_MODES,
        experience_levels=EXPERIENCE_LEVELS
    )


@employer_bp.route('/jobs/<int:job_id>/toggle-status', methods=['POST'])
@employer_required
def toggle_job_status(job_id):
    user = get_current_user()
    job = db.session.get(Job, job_id)
    if not job or job.employer_id != user.id:
        abort(403)

    job.status = 'Closed' if job.status == 'Open' else 'Open'
    db.session.commit()
    flash(f'Job status changed to {job.status}.', 'info')
    return redirect(url_for('employer.manage_jobs'))


@employer_bp.route('/jobs/<int:job_id>/delete', methods=['POST'])
@employer_required
def delete_job(job_id):
    user = get_current_user()
    job = db.session.get(Job, job_id)
    if not job or job.employer_id != user.id:
        abort(403)

    db.session.delete(job)
    db.session.commit()
    flash('Job posting deleted successfully.', 'success')
    return redirect(url_for('employer.manage_jobs'))


@employer_bp.route('/applicants')
@employer_bp.route('/jobs/<int:job_id>/applicants')
@employer_required
def applicants(job_id=None):
    user = get_current_user()
    employer_jobs = Job.query.filter_by(employer_id=user.id).all()
    job_ids = [j.id for j in employer_jobs]

    if not job_ids:
        return render_template(
            'employer/applicants.html',
            applications=[],
            employer_jobs=[],
            selected_job_id=job_id,
            selected_status=None,
            statuses=APPLICATION_STATUSES
        )

    query = Application.query.filter(Application.job_id.in_(job_ids))
    if job_id:
        # Check if job belongs to this employer
        current_job = db.session.get(Job, job_id)
        if not current_job or current_job.employer_id != user.id:
            abort(403)
        query = query.filter_by(job_id=job_id)

    status_filter = request.args.get('status', '').strip()
    if status_filter and status_filter != 'All':
        query = query.filter_by(status=status_filter)

    applications_list = query.order_by(Application.applied_at.desc()).all()

    return render_template(
        'employer/applicants.html',
        applications=applications_list,
        employer_jobs=employer_jobs,
        selected_job_id=job_id,
        selected_status=status_filter,
        statuses=APPLICATION_STATUSES
    )


@employer_bp.route('/applications/<int:app_id>/status', methods=['POST'])
@employer_required
def update_status(app_id):
    user = get_current_user()
    new_status = request.form.get('status', '').strip()
    success, msg = update_application_status(app_id, new_status, user)

    if success:
        flash(msg, 'success')
    else:
        flash(msg, 'danger')

    return redirect(request.referrer or url_for('employer.applicants'))


@employer_bp.route('/download-resume/<int:app_id>')
@employer_required
def download_resume(app_id):
    user = get_current_user()
    application = db.session.get(Application, app_id)
    if not application:
        abort(404)

    # Employer authorization check
    if application.job.employer_id != user.id:
        abort(403)

    if not application.resume_path:
        flash('Candidate has not attached a resume.', 'warning')
        return redirect(url_for('employer.applicants'))

    download_filename = f"Resume_{application.candidate.name.replace(' ', '_')}.pdf"
    return send_from_directory(
        Config.RESUME_FOLDER,
        application.resume_path,
        as_attachment=True,
        download_name=download_filename
    )


@employer_bp.route('/candidate/<int:candidate_id>/profile')
@employer_required
def view_candidate_profile(candidate_id):
    candidate = db.session.get(User, candidate_id)
    if not candidate or candidate.role != 'candidate':
        abort(404)
    return render_template('employer/candidate-modal-view.html', candidate=candidate)
