from extensions import db
from models.application import Application
from models.saved_job import SavedJob
from models.job import Job
from models.user import User


def has_applied(job_id, candidate_id):
    """Check if candidate has already submitted an application for the given job."""
    return Application.query.filter_by(job_id=job_id, candidate_id=candidate_id).first() is not None


def is_job_saved(job_id, candidate_id):
    """Check if job is saved/bookmarked by candidate."""
    return SavedJob.query.filter_by(job_id=job_id, candidate_id=candidate_id).first() is not None


def toggle_save_job(job_id, candidate_id):
    """
    Saves or unsaves a job for a candidate.
    Returns: (is_now_saved: bool, message: str)
    """
    saved = SavedJob.query.filter_by(job_id=job_id, candidate_id=candidate_id).first()
    if saved:
        db.session.delete(saved)
        db.session.commit()
        return False, "Job removed from saved list."
    else:
        new_save = SavedJob(job_id=job_id, candidate_id=candidate_id)
        db.session.add(new_save)
        db.session.commit()
        return True, "Job saved successfully."


def submit_application(job_id, candidate_id, resume_path=None, cover_letter=None,
                       applicant_name=None, applicant_email=None, applicant_phone=None,
                       applicant_location=None, experience=None, qualification=None, skills=None):
    """
    Submits a new job application.
    Validates job status and checks for existing duplicate applications.
    Stores entered applicant information and attached resume.
    """
    job = db.session.get(Job, job_id)
    if not job:
        return None, "Job not found."

    if job.status != 'Open':
        return None, "Applications for this job are currently closed."

    if has_applied(job_id, candidate_id):
        return None, "You have already applied for this job."

    candidate = db.session.get(User, candidate_id)

    # Defaults if not explicitly provided
    if not applicant_name and candidate:
        applicant_name = candidate.name
    if not applicant_email and candidate:
        applicant_email = candidate.email
    if not applicant_phone and candidate:
        applicant_phone = candidate.phone
    if not applicant_location and candidate:
        applicant_location = candidate.location
    if candidate and candidate.candidate_profile:
        if not experience:
            experience = candidate.candidate_profile.experience
        if not qualification:
            qualification = candidate.candidate_profile.qualification or candidate.candidate_profile.education
        if not skills:
            skills = candidate.candidate_profile.skills
        if not resume_path:
            resume_path = candidate.candidate_profile.resume_path

    if not resume_path:
        return None, "A resume document is required to submit your application."

    application = Application(
        job_id=job_id,
        candidate_id=candidate_id,
        applicant_name=applicant_name.strip() if applicant_name else None,
        applicant_email=applicant_email.strip() if applicant_email else None,
        applicant_phone=applicant_phone.strip() if applicant_phone else None,
        applicant_location=applicant_location.strip() if applicant_location else None,
        experience=experience.strip() if experience else None,
        qualification=qualification.strip() if qualification else None,
        skills=skills.strip() if skills else None,
        resume_path=resume_path,
        cover_letter=cover_letter.strip() if cover_letter else None,
        status='Applied'
    )
    db.session.add(application)
    db.session.commit()

    # Dispatch notifications
    from services.notification_service import create_notification, notify_admin
    cand_name = applicant_name or (candidate.name if candidate else "A candidate")

    # 1. Notify Candidate
    create_notification(
        candidate_id,
        "Application Submitted Successfully",
        f"Your application for '{job.title}' at {job.company.company_name if job.company else 'Employer'} has been submitted and sent to the administrator for review.",
        link="/candidate/applications"
    )

    # 2. Notify Job Employer
    if job.employer_id != candidate_id:
        create_notification(
            job.employer_id,
            "New Applicant Received",
            f"{cand_name} applied for '{job.title}'.",
            link=f"/employer/jobs/{job.id}/applicants"
        )

    # 3. Notify Admin
    notify_admin(
        "New Job Application Submitted",
        f"{cand_name} ({applicant_email or (candidate.email if candidate else '')}) applied for '{job.title}'. Please review details and update application status.",
        link="/admin/applications"
    )

    return application, None


def update_application_status(application_id, new_status, current_user, admin_notes=None):
    """
    Allows employer who owns the job or admin to update applicant status and provide feedback notes.
    """
    valid_statuses = ['Applied', 'Under Review', 'Shortlisted', 'Interview', 'Rejected', 'Selected']
    if new_status not in valid_statuses:
        return False, f"Invalid status: {new_status}"

    application = db.session.get(Application, application_id)
    if not application:
        return False, "Application not found."

    # Authorization check: either admin or the job's employer
    if current_user.role != 'admin' and application.job.employer_id != current_user.id:
        return False, "Unauthorized to update this application."

    application.status = new_status
    if admin_notes is not None:
        application.admin_notes = admin_notes.strip() if admin_notes.strip() else None
    db.session.commit()

    # Dispatch status notifications
    from services.notification_service import create_notification, notify_admin

    # 1. Notify Candidate immediately
    note_extra = f" Recruiter note: {application.admin_notes}" if application.admin_notes else ""
    create_notification(
        application.candidate_id,
        f"Application Status: {new_status}",
        f"Your application for '{application.job.title}' has been updated to '{new_status}'.{note_extra}",
        link="/candidate/applications"
    )

    # 2. Notify other party (Admin or Employer)
    if current_user.role == 'admin':
        if application.job.employer_id != current_user.id:
            create_notification(
                application.job.employer_id,
                "Application Status Updated by Admin",
                f"Administrator updated {application.candidate.name}'s application for '{application.job.title}' to '{new_status}'.",
                link=f"/employer/jobs/{application.job.id}/applicants"
            )
    else:
        notify_admin(
            "Application Status Updated",
            f"Employer {current_user.name} updated {application.candidate.name}'s application for '{application.job.title}' to '{new_status}'.",
            link="/admin/applications"
        )

    return True, f"Application status updated to '{new_status}'."
