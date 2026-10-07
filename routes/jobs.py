from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort
from extensions import db
from models.job import Job
from models.company import Company
from models.application import Application
from services.auth_service import get_current_user, candidate_required
from services.job_service import search_jobs, get_popular_categories
from services.application_service import has_applied, is_job_saved, toggle_save_job, submit_application
from services.file_service import save_resume

jobs_bp = Blueprint('jobs', __name__)

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


@jobs_bp.route('/jobs')
def list_jobs():
    keyword = request.args.get('q', '').strip()
    location = request.args.get('location', '').strip()
    category = request.args.get('category', '').strip()
    job_type = request.args.get('job_type', '').strip()
    work_mode = request.args.get('work_mode', '').strip()
    experience_level = request.args.get('experience_level', '').strip()
    min_salary = request.args.get('min_salary', '').strip()
    sort_by = request.args.get('sort', 'newest').strip()
    page = request.args.get('page', 1, type=int)

    pagination = search_jobs(
        keyword=keyword,
        location=location,
        category=category,
        job_type=job_type,
        work_mode=work_mode,
        experience_level=experience_level,
        min_salary=min_salary,
        sort_by=sort_by,
        page=page,
        per_page=9
    )

    current_user = get_current_user()
    saved_job_ids = set()
    applied_job_ids = set()
    if current_user and current_user.role == 'candidate':
        saved_job_ids = {s.job_id for s in current_user.saved_jobs}
        applied_job_ids = {a.job_id for a in current_user.applications}

    return render_template(
        'jobs.html',
        pagination=pagination,
        jobs=pagination.items,
        total_count=pagination.total,
        keyword=keyword,
        location=location,
        selected_category=category,
        selected_job_type=job_type,
        selected_work_mode=work_mode,
        selected_experience=experience_level,
        min_salary=min_salary,
        sort_by=sort_by,
        categories=CATEGORIES,
        job_types=JOB_TYPES,
        work_modes=WORK_MODES,
        experience_levels=EXPERIENCE_LEVELS,
        saved_job_ids=saved_job_ids,
        applied_job_ids=applied_job_ids
    )


@jobs_bp.route('/jobs/<int:job_id>')
def job_details(job_id):
    job = db.session.get(Job, job_id)
    if not job:
        abort(404)

    current_user = get_current_user()
    user_has_applied = False
    user_saved = False
    existing_application = None

    if current_user and current_user.role == 'candidate':
        user_has_applied = has_applied(job.id, current_user.id)
        user_saved = is_job_saved(job.id, current_user.id)
        if user_has_applied:
            existing_application = Application.query.filter_by(job_id=job.id, candidate_id=current_user.id).first()

    # Similar jobs in same category
    similar_jobs = Job.query.filter(
        Job.category == job.category,
        Job.id != job.id,
        Job.status == 'Open'
    ).limit(3).all()

    return render_template(
        'job-details.html',
        job=job,
        user_has_applied=user_has_applied,
        user_saved=user_saved,
        existing_application=existing_application,
        similar_jobs=similar_jobs
    )


@jobs_bp.route('/jobs/<int:job_id>/apply', methods=['POST'])
@candidate_required
def apply_job(job_id):
    job = db.session.get(Job, job_id)
    if not job:
        abort(404)

    current_user = get_current_user()

    # Read required form fields
    applicant_name = request.form.get('applicant_name', '').strip()
    applicant_email = request.form.get('applicant_email', '').strip().lower()
    applicant_phone = request.form.get('applicant_phone', '').strip()
    applicant_location = request.form.get('applicant_location', '').strip()
    experience = request.form.get('experience', '').strip()
    qualification = request.form.get('qualification', '').strip()
    skills = request.form.get('skills', '').strip()
    cover_letter = request.form.get('cover_letter', '').strip()

    # Fallback to current_user if empty
    if not applicant_name:
        applicant_name = current_user.name
    if not applicant_email:
        applicant_email = current_user.email
    if not applicant_phone and current_user.phone:
        applicant_phone = current_user.phone
    if not applicant_location and current_user.location:
        applicant_location = current_user.location

    # Comprehensive field validation
    if not applicant_name or not applicant_email or not applicant_phone or not applicant_location:
        flash('Please fill in all mandatory personal details: Full Name, Email, Phone, and Location.', 'danger')
        return redirect(url_for('jobs.job_details', job_id=job_id))

    if not experience or not qualification or not skills:
        flash('Please complete all professional qualification fields: Total Experience, Highest Qualification, and Key Skills.', 'danger')
        return redirect(url_for('jobs.job_details', job_id=job_id))

    # Handle resume upload
    resume_file = request.files.get('resume')
    resume_path = None
    if resume_file and resume_file.filename and resume_file.filename.strip():
        filename, err = save_resume(resume_file)
        if err:
            flash(f"Resume upload error: {err}", 'danger')
            return redirect(url_for('jobs.job_details', job_id=job_id))
        resume_path = filename
        # Also store to candidate profile if profile had no resume
        profile = current_user.candidate_profile
        if profile and not profile.resume_path:
            profile.resume_path = filename
            clean_name = resume_file.filename.replace('\\', '/').split('/')[-1].strip()
            profile.resume_filename = clean_name or f"resume_{current_user.id}.pdf"
            db.session.commit()

    # If no file uploaded now, fall back to candidate's existing resume on file
    profile = current_user.candidate_profile
    if not resume_path and profile and profile.resume_path:
        resume_path = profile.resume_path

    if not resume_path:
        flash('A Resume document is required to submit your application. Please select and upload your resume (PDF, DOC, DOCX, RTF, or TXT).', 'danger')
        return redirect(url_for('jobs.job_details', job_id=job_id))

    # Enrich candidate profile with any newly provided details if empty
    if profile:
        if not profile.experience and experience:
            profile.experience = experience
        if not profile.qualification and qualification:
            profile.qualification = qualification
        if not profile.skills and skills:
            profile.skills = skills
        if not current_user.phone and applicant_phone:
            current_user.phone = applicant_phone
        if not current_user.location and applicant_location:
            current_user.location = applicant_location
        db.session.commit()

    application, err = submit_application(
        job_id=job_id,
        candidate_id=current_user.id,
        resume_path=resume_path,
        cover_letter=cover_letter,
        applicant_name=applicant_name,
        applicant_email=applicant_email,
        applicant_phone=applicant_phone,
        applicant_location=applicant_location,
        experience=experience,
        qualification=qualification,
        skills=skills
    )

    if err:
        flash(err, 'warning')
    else:
        flash(f'Your application for "{job.title}" has been submitted successfully! The administration team has received your application and will review your qualifications.', 'success')

    return redirect(url_for('jobs.job_details', job_id=job_id))


@jobs_bp.route('/jobs/<int:job_id>/save', methods=['POST'])
@candidate_required
def save_job(job_id):
    job = db.session.get(Job, job_id)
    if not job:
        abort(404)

    current_user = get_current_user()
    is_saved, msg = toggle_save_job(job_id, current_user.id)

    # Support AJAX response
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
        return jsonify({'success': True, 'saved': is_saved, 'message': msg})

    flash(msg, 'success' if is_saved else 'info')
    return redirect(request.referrer or url_for('jobs.job_details', job_id=job_id))


@jobs_bp.route('/companies')
def list_companies():
    companies = Company.query.join(Job, isouter=True).order_by(Company.company_name.asc()).all()
    return render_template('companies.html', companies=companies)


@jobs_bp.route('/companies/<int:company_id>')
def company_details(company_id):
    company = db.session.get(Company, company_id)
    if not company:
        abort(404)
    open_jobs = Job.query.filter_by(company_id=company.id, status='Open').order_by(Job.created_at.desc()).all()
    return render_template('company-details.html', company=company, jobs=open_jobs)
