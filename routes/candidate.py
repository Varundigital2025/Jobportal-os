import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_from_directory, abort, session
from extensions import db
from models.user import User
from models.candidate import CandidateProfile
from models.application import Application
from models.saved_job import SavedJob
from services.auth_service import get_current_user, candidate_required
from services.file_service import save_resume, save_profile_photo
from config import Config

candidate_bp = Blueprint('candidate', __name__, url_prefix='/candidate')


@candidate_bp.route('/dashboard')
@candidate_required
def dashboard():
    user = get_current_user()
    profile = user.candidate_profile
    if not profile:
        profile = CandidateProfile(user_id=user.id)
        db.session.add(profile)
        db.session.commit()

    # Statistics
    all_apps = Application.query.filter_by(candidate_id=user.id).all()
    total_applications = len(all_apps)
    under_review_count = sum(1 for a in all_apps if a.status == 'Under Review')
    shortlisted_count = sum(1 for a in all_apps if a.status == 'Shortlisted')
    interview_count = sum(1 for a in all_apps if a.status == 'Interview')
    saved_jobs_count = SavedJob.query.filter_by(candidate_id=user.id).count()

    # Recent applications (last 5)
    recent_applications = Application.query.filter_by(candidate_id=user.id)\
        .order_by(Application.applied_at.desc()).limit(5).all()

    # Recent saved jobs (last 4)
    recent_saved_jobs = SavedJob.query.filter_by(candidate_id=user.id)\
        .order_by(SavedJob.created_at.desc()).limit(4).all()

    return render_template(
        'candidate/dashboard.html',
        user=user,
        profile=profile,
        total_applications=total_applications,
        under_review_count=under_review_count,
        shortlisted_count=shortlisted_count,
        interview_count=interview_count,
        saved_jobs_count=saved_jobs_count,
        recent_applications=recent_applications,
        recent_saved_jobs=recent_saved_jobs
    )


@candidate_bp.route('/profile', methods=['GET', 'POST'])
@candidate_required
def profile():
    user = get_current_user()
    c_profile = user.candidate_profile
    if not c_profile:
        c_profile = CandidateProfile(user_id=user.id)
        db.session.add(c_profile)
        db.session.commit()

    if request.method == 'POST':
        user.name = request.form.get('name', user.name).strip()
        user.phone = request.form.get('phone', '').strip()
        user.location = request.form.get('location', '').strip()
        session['user_name'] = user.name

        c_profile.headline = request.form.get('headline', '').strip()
        c_profile.bio = request.form.get('bio', '').strip()
        c_profile.skills = request.form.get('skills', '').strip()
        c_profile.experience = request.form.get('experience', '').strip()
        c_profile.education = request.form.get('education', '').strip()
        c_profile.qualification = request.form.get('qualification', '').strip()
        c_profile.linkedin_url = request.form.get('linkedin_url', '').strip()
        c_profile.portfolio_url = request.form.get('portfolio_url', '').strip()

        has_upload_error = False

        # Handle profile photo upload
        photo_file = request.files.get('profile_photo')
        if photo_file and photo_file.filename and photo_file.filename.strip():
            filename, err = save_profile_photo(photo_file)
            if err:
                flash(f"Profile photo error: {err}", 'danger')
                has_upload_error = True
            else:
                user.profile_photo = filename

        # Handle resume upload from profile page if provided
        resume_file = request.files.get('resume')
        if resume_file and resume_file.filename and resume_file.filename.strip():
            filename, err = save_resume(resume_file)
            if err:
                flash(f"Resume error: {err}", 'danger')
                has_upload_error = True
            else:
                c_profile.resume_path = filename
                clean_name = resume_file.filename.replace('\\', '/').split('/')[-1].strip()
                c_profile.resume_filename = clean_name or f"resume_{user.id}.pdf"

        db.session.commit()

        if not has_upload_error:
            flash('Your profile has been updated successfully!', 'success')
        else:
            flash('Profile text saved, but some file uploads could not be processed. Please see details above.', 'warning')
        return redirect(url_for('candidate.profile'))

    return render_template('candidate/profile.html', user=user, profile=c_profile)


@candidate_bp.route('/resume', methods=['GET', 'POST'])
@candidate_required
def resume():
    user = get_current_user()
    c_profile = user.candidate_profile
    if not c_profile:
        c_profile = CandidateProfile(user_id=user.id)
        db.session.add(c_profile)
        db.session.commit()

    if request.method == 'POST':
        resume_file = request.files.get('resume')
        if not resume_file or not resume_file.filename:
            flash('Please select a resume file to upload (PDF, DOC, or DOCX).', 'warning')
            return redirect(url_for('candidate.resume'))

        filename, err = save_resume(resume_file)
        if err:
            flash(err, 'danger')
            return redirect(url_for('candidate.resume'))

        c_profile.resume_path = filename
        c_profile.resume_filename = resume_file.filename
        db.session.commit()
        flash('Resume uploaded and attached to your profile successfully!', 'success')
        return redirect(url_for('candidate.resume'))

    return render_template('candidate/resume.html', user=user, profile=c_profile)


@candidate_bp.route('/resume/download')
@candidate_required
def download_resume():
    user = get_current_user()
    c_profile = user.candidate_profile
    if not c_profile or not c_profile.resume_path:
        flash('No resume has been uploaded yet.', 'warning')
        return redirect(url_for('candidate.resume'))

    return send_from_directory(
        Config.RESUME_FOLDER,
        c_profile.resume_path,
        as_attachment=True,
        download_name=c_profile.resume_filename or 'resume.pdf'
    )


@candidate_bp.route('/applications')
@candidate_required
def applications():
    user = get_current_user()
    status_filter = request.args.get('status', '').strip()
    query = Application.query.filter_by(candidate_id=user.id)

    if status_filter and status_filter != 'All':
        query = query.filter_by(status=status_filter)

    user_applications = query.order_by(Application.applied_at.desc()).all()
    statuses = ['Applied', 'Under Review', 'Shortlisted', 'Interview', 'Rejected', 'Selected']

    return render_template(
        'candidate/applications.html',
        applications=user_applications,
        selected_status=status_filter,
        statuses=statuses
    )


@candidate_bp.route('/saved-jobs')
@candidate_required
def saved_jobs():
    user = get_current_user()
    saved = SavedJob.query.filter_by(candidate_id=user.id).order_by(SavedJob.created_at.desc()).all()
    return render_template('candidate/saved-jobs.html', saved_jobs=saved)


@candidate_bp.route('/settings', methods=['GET', 'POST'])
@candidate_required
def settings():
    user = get_current_user()
    c_profile = user.candidate_profile
    if not c_profile:
        c_profile = CandidateProfile(user_id=user.id)
        db.session.add(c_profile)
        db.session.commit()

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'change_password':
            current_password = request.form.get('current_password', '')
            new_password = request.form.get('new_password', '')
            confirm_password = request.form.get('confirm_password', '')

            if not current_password or not new_password:
                flash('Please provide both current and new password.', 'warning')
                return redirect(url_for('candidate.settings'))

            if not user.check_password(current_password):
                flash('Current password entered is incorrect.', 'danger')
                return redirect(url_for('candidate.settings'))

            if len(new_password) < 6:
                flash('New password must be at least 6 characters long.', 'danger')
                return redirect(url_for('candidate.settings'))

            if new_password != confirm_password:
                flash('New password and confirmation do not match.', 'danger')
                return redirect(url_for('candidate.settings'))

            user.set_password(new_password)
            db.session.commit()

            # Dispatch notification
            from services.notification_service import create_notification
            create_notification(
                user.id,
                "Security Alert: Password Changed",
                "Your account password was updated successfully.",
                link="/candidate/settings"
            )

            flash('Your account password has been updated successfully!', 'success')
            return redirect(url_for('candidate.settings'))

        elif action == 'update_photo':
            photo_file = request.files.get('profile_photo')
            if photo_file and photo_file.filename and photo_file.filename.strip():
                filename, err = save_profile_photo(photo_file)
                if err:
                    flash(f"Profile photo error: {err}", 'danger')
                else:
                    user.profile_photo = filename
                    db.session.commit()
                    flash('Profile photo updated successfully!', 'success')
            else:
                flash('Please select an image file to upload.', 'warning')
            return redirect(url_for('candidate.settings'))

        elif action == 'remove_photo':
            user.profile_photo = None
            db.session.commit()
            flash('Profile photo has been removed.', 'info')
            return redirect(url_for('candidate.settings'))

        elif action == 'update_resume':
            resume_file = request.files.get('resume')
            if resume_file and resume_file.filename and resume_file.filename.strip():
                filename, err = save_resume(resume_file)
                if err:
                    flash(f"Resume upload error: {err}", 'danger')
                else:
                    c_profile.resume_path = filename
                    clean_name = resume_file.filename.replace('\\', '/').split('/')[-1].strip()
                    c_profile.resume_filename = clean_name or f"resume_{user.id}.pdf"
                    db.session.commit()
                    flash('Resume updated and saved to your profile successfully!', 'success')
            else:
                flash('Please select a resume document to upload (PDF, DOC, DOCX).', 'warning')
            return redirect(url_for('candidate.settings'))

        elif action == 'remove_resume':
            c_profile.resume_path = None
            c_profile.resume_filename = None
            db.session.commit()
            flash('Resume has been removed from your profile.', 'info')
            return redirect(url_for('candidate.settings'))

        elif action in ('update_account', 'update_contact'):
            name = request.form.get('name', '').strip()
            if name:
                user.name = name
                session['user_name'] = user.name
            user.phone = request.form.get('phone', '').strip()
            user.location = request.form.get('location', '').strip()
            db.session.commit()
            flash('Account contact settings saved successfully.', 'success')
            return redirect(url_for('candidate.settings'))

    return render_template('candidate/settings.html', user=user, profile=c_profile)
