"""
Comprehensive End-to-End Automated Test Suite for JobPortal
Validates:
1. Authentication & Registration (Candidate, Employer, Admin)
2. Role-based Authorization Boundaries (403 / Redirects)
3. Candidate Workflow (Profile, Resume, Search, Save, Apply, Duplicate Block)
4. Employer Workflow (Company Profile, Job Posting, Edit, Applicant Review, Status Update)
5. Admin Workflow (Platform Stats, User Moderation, Job Moderation)
6. Data Integrity & Constraints (Duplicate Email, Duplicate Application, 404s)
"""
import unittest
import io
import uuid
from app import create_app
from extensions import db
from models.user import User
from models.candidate import CandidateProfile
from models.company import Company
from models.job import Job
from models.application import Application
from models.saved_job import SavedJob
from models.notification import Notification


class JobPortalComprehensiveTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()

    def test_01_public_pages(self):
        """Test homepage, jobs list, companies, and about pages."""
        # Home
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Find the right job', res.data)
        self.assertIn(b'Popular Job Categories', res.data)

        # Jobs listing
        res = self.client.get('/jobs')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Explore Job Opportunities', res.data)

        # Companies
        res = self.client.get('/companies')
        self.assertEqual(res.status_code, 200)

        # About
        res = self.client.get('/about')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'About Our Platform', res.data)

    def test_02_job_search_and_filters(self):
        """Test search by keyword, location, and filters against database."""
        # Keyword search
        res = self.client.get('/jobs?q=Python')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Python', res.data)

        # Location filter
        res = self.client.get('/jobs?location=Remote')
        self.assertEqual(res.status_code, 200)

        # Category filter
        res = self.client.get('/jobs?category=Software+%26+Engineering')
        self.assertEqual(res.status_code, 200)

        # Work mode filter
        res = self.client.get('/jobs?work_mode=Remote')
        self.assertEqual(res.status_code, 200)

        # Non-existent search returns graceful empty state
        res = self.client.get('/jobs?q=NonExistentKeywordXYZ123')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'No jobs match your search criteria', res.data)

    def test_03_candidate_workflow(self):
        """Test Candidate registration, login, profile edit, job save, and application."""
        unique_email = f"tester.cand.{uuid.uuid4().hex[:8]}@example.com"

        # 1. Register
        res = self.client.post('/auth/register', data={
            'name': 'Test Candidate',
            'email': unique_email,
            'password': 'Password@123',
            'confirm_password': 'Password@123',
            'role': 'candidate',
            'phone': '+1 555-0101',
            'location': 'Denver, CO'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        # Check user in DB
        with self.app.app_context():
            u = User.query.filter_by(email=unique_email).first()
            self.assertIsNotNone(u)
            self.assertEqual(u.role, 'candidate')
            self.assertIsNotNone(u.candidate_profile)
            user_id = u.id

        # 2. Update Profile & Upload Resume
        fake_resume = (io.BytesIO(b"%PDF-1.4 Mock resume content for testing"), 'test_resume.pdf')
        res = self.client.post('/candidate/profile', data={
            'name': 'Test Candidate Updated',
            'phone': '+1 555-9999',
            'location': 'Boulder, CO',
            'headline': 'Senior Software Architect',
            'bio': 'Experienced tester with passion for quality code.',
            'skills': 'Python, Flask, PyTest, SQLite',
            'experience': '7 years testing software.',
            'education': 'M.S. in Software Systems',
            'qualification': 'Master of Science',
            'linkedin_url': 'https://linkedin.com/in/testcandidate',
            'portfolio_url': 'https://testcandidate.dev',
            'resume': fake_resume
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Your profile has been updated successfully', res.data)

        # Verify profile score in DB
        with self.app.app_context():
            u = db.session.get(User, user_id)
            self.assertEqual(u.name, 'Test Candidate Updated')
            self.assertGreater(u.candidate_profile.completion_percentage, 50)
            self.assertIsNotNone(u.candidate_profile.resume_path)

        # 3. Save a Job
        with self.app.app_context():
            open_job = Job.query.filter_by(status='Open').first()
            job_id = open_job.id

        res = self.client.post(f'/jobs/{job_id}/save', follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        with self.app.app_context():
            saved = SavedJob.query.filter_by(candidate_id=user_id, job_id=job_id).first()
            self.assertIsNotNone(saved)

        # Verify saved jobs page
        res = self.client.get('/candidate/saved-jobs')
        self.assertEqual(res.status_code, 200)

        # 4. Apply for the Job
        res = self.client.post(f'/jobs/{job_id}/apply', data={
            'applicant_name': 'Test Candidate Updated',
            'applicant_email': unique_email,
            'applicant_phone': '+1 555-9999',
            'applicant_location': 'Boulder, CO',
            'experience': '7 years',
            'qualification': 'Master of Science',
            'skills': 'Python, Flask, PyTest, SQLite',
            'cover_letter': 'I am thrilled to apply for this opening. Please find my credentials attached.'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'submitted successfully', res.data)

        # Verify application in DB with full candidate details
        with self.app.app_context():
            app_rec = Application.query.filter_by(candidate_id=user_id, job_id=job_id).first()
            self.assertIsNotNone(app_rec)
            self.assertEqual(app_rec.status, 'Applied')
            self.assertEqual(app_rec.applicant_name, 'Test Candidate Updated')
            self.assertEqual(app_rec.applicant_email, unique_email)
            self.assertEqual(app_rec.applicant_phone, '+1 555-9999')
            self.assertEqual(app_rec.applicant_location, 'Boulder, CO')
            self.assertEqual(app_rec.experience, '7 years')
            self.assertEqual(app_rec.qualification, 'Master of Science')
            self.assertEqual(app_rec.skills, 'Python, Flask, PyTest, SQLite')

        # 5. Prevent Duplicate Application
        res = self.client.post(f'/jobs/{job_id}/apply', data={
            'applicant_name': 'Test Candidate Updated',
            'applicant_email': unique_email,
            'applicant_phone': '+1 555-9999',
            'applicant_location': 'Boulder, CO',
            'experience': '7 years',
            'qualification': 'Master of Science',
            'skills': 'Python, Flask, PyTest, SQLite',
            'cover_letter': 'Trying to apply a second time.'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'You have already applied for this job', res.data)

        # 6. Verify Candidate Dashboard
        res = self.client.get('/candidate/dashboard')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Applied', res.data)

        # Logout
        self.client.get('/auth/logout')

    def test_04_employer_workflow(self):
        """Test Employer registration, company profile, posting job, and reviewing applicants."""
        unique_emp_email = f"tester.emp.{uuid.uuid4().hex[:8]}@example.com"

        # 1. Register Employer (employers are created via auth_service / admin, public registration is candidate-only)
        from services.auth_service import register_user
        with self.app.app_context():
            emp_user, err = register_user(
                name='Hiring Manager Bob',
                email=unique_emp_email,
                password='Password@123',
                role='employer',
                company_name='Horizon Dynamics Inc',
                phone='+1 555-8888',
                location='Dallas, TX'
            )
            self.assertIsNone(err)
            self.assertIsNotNone(emp_user)
            self.assertEqual(emp_user.role, 'employer')
            self.assertIsNotNone(emp_user.company)
            emp_id = emp_user.id

        # Employer logs in
        login_res = self.client.post('/auth/login', data={
            'email': unique_emp_email,
            'password': 'Password@123'
        }, follow_redirects=True)
        self.assertEqual(login_res.status_code, 200)

        # 2. Update Company Profile
        res = self.client.post('/employer/company-profile', data={
            'company_name': 'Horizon Dynamics Inc',
            'industry': 'Aerospace & Robotics',
            'company_size': '51-200',
            'website': 'https://horizondynamics.example.com',
            'location': 'Dallas, TX',
            'phone': '+1 555-8888',
            'description': 'Building next-generation robotics software.'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Company profile updated successfully', res.data)

        # 3. Post a New Job
        res = self.client.post('/employer/jobs/create', data={
            'title': 'Autonomous Systems Engineer',
            'category': 'Software & Engineering',
            'location': 'Dallas, TX',
            'job_type': 'Full Time',
            'work_mode': 'On-site',
            'experience_level': 'Senior Level',
            'salary_min': '130000',
            'salary_max': '165000',
            'salary_currency': '$',
            'skills': 'C++, Python, ROS, Linux',
            'description': 'Develop autonomous control algorithms and vehicle motion planning software.',
            'responsibilities': 'Write low-latency trajectory algorithms.',
            'requirements': '5+ years in autonomous systems or robotics.',
            'status': 'Open'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'posted successfully', res.data)

        # Verify job in DB
        with self.app.app_context():
            created_job = Job.query.filter_by(employer_id=emp_id, title='Autonomous Systems Engineer').first()
            self.assertIsNotNone(created_job)
            created_job_id = created_job.id

        # 4. Edit the Job
        res = self.client.post(f'/employer/jobs/{created_job_id}/edit', data={
            'title': 'Senior Autonomous Systems Engineer',
            'category': 'Software & Engineering',
            'location': 'Dallas, TX',
            'job_type': 'Full Time',
            'work_mode': 'Hybrid',
            'experience_level': 'Senior Level',
            'salary_min': '140000',
            'salary_max': '175000',
            'salary_currency': '$',
            'skills': 'C++, Python, ROS, Linux, Docker',
            'description': 'Updated description with higher compensation.',
            'responsibilities': 'Lead team of autonomous robotics developers.',
            'requirements': '6+ years in robotics.',
            'status': 'Open'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'updated successfully', res.data)

        # 5. Candidate applies to this employer's job
        with self.app.app_context():
            cand = User.query.filter_by(role='candidate').first()
            cand_id = cand.id

        # Simulate candidate applying
        with self.client.session_transaction() as sess:
            sess['user_id'] = cand_id
            sess['role'] = 'candidate'

        dummy_cv = (io.BytesIO(b'%PDF-1.4 Mock CV Content'), 'candidate_cv.pdf')
        self.client.post(f'/jobs/{created_job_id}/apply', data={
            'applicant_name': 'Candidate Review Applicant',
            'applicant_email': cand.email,
            'applicant_phone': '+1 555-4321',
            'applicant_location': 'Dallas, TX',
            'experience': '5 years',
            'qualification': 'B.S. Robotics',
            'skills': 'ROS, C++, Python',
            'cover_letter': 'Candidate application for testing employer review.',
            'resume': dummy_cv
        }, content_type='multipart/form-data')

        # Switch back to employer session
        with self.client.session_transaction() as sess:
            sess['user_id'] = emp_id
            sess['role'] = 'employer'

        # 6. Employer reviews applicants
        res = self.client.get(f'/employer/jobs/{created_job_id}/applicants')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Candidate application for testing employer review', res.data)

        # 7. Employer changes application status to 'Shortlisted'
        with self.app.app_context():
            app_record = Application.query.filter_by(job_id=created_job_id, candidate_id=cand_id).first()
            app_id = app_record.id

        res = self.client.post(f'/employer/applications/{app_id}/status', data={
            'status': 'Shortlisted'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        with self.app.app_context():
            updated_app = db.session.get(Application, app_id)
            self.assertEqual(updated_app.status, 'Shortlisted')

        self.client.get('/auth/logout')

    def test_05_admin_workflow(self):
        """Test Administrator login, statistics, user moderation, and job moderation."""
        # 1. Login as Admin
        res = self.client.post('/auth/login', data={
            'email': 'admin@jobportal.local',
            'password': 'AdminPassword@2026'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        # 2. View Admin Dashboard
        res = self.client.get('/admin/dashboard')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Platform Analytics', res.data)
        self.assertIn(b'Total Users', res.data)

        # 3. View Users & Toggle Status
        res = self.client.get('/admin/users')
        self.assertEqual(res.status_code, 200)

        with self.app.app_context():
            cand_user = User.query.filter_by(role='candidate').first()
            cand_id = cand_user.id
            init_status = cand_user.is_active

        res = self.client.post(f'/admin/users/{cand_id}/toggle-status', follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        with self.app.app_context():
            cand_user_after = db.session.get(User, cand_id)
            self.assertNotEqual(cand_user_after.is_active, init_status)

        # Toggle back to active
        self.client.post(f'/admin/users/{cand_id}/toggle-status', follow_redirects=True)

        # 4. View Jobs & Change Status
        with self.app.app_context():
            job = Job.query.first()
            job_id = job.id

        res = self.client.post(f'/admin/jobs/{job_id}/status', data={'status': 'Closed'}, follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        with self.app.app_context():
            mod_job = db.session.get(Job, job_id)
            self.assertEqual(mod_job.status, 'Closed')

        # Re-open
        self.client.post(f'/admin/jobs/{job_id}/status', data={'status': 'Open'}, follow_redirects=True)

        # 5. View Applications Log
        res = self.client.get('/admin/applications')
        self.assertEqual(res.status_code, 200)

        # 6. Admin creates a new job post that reflects in website
        res = self.client.post('/admin/jobs/create', data={
            'title': 'Principal Systems Architect (Admin Posted)',
            'category': 'Software & Engineering',
            'location': 'Remote',
            'job_type': 'Full Time',
            'work_mode': 'Remote',
            'experience_level': 'Lead / Manager',
            'salary_min': '180000',
            'salary_max': '220000',
            'salary_currency': '$',
            'skills': 'Distributed Systems, Python, Kubernetes, Go',
            'description': 'Architect platform-wide high throughput distributed services.',
            'responsibilities': 'Set technical vision and guide engineering architecture.',
            'requirements': '10+ years in distributed architectures.',
            'status': 'Open'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'posted successfully by Admin and is now live on the website', res.data)

        # Verify new admin job immediately reflects on public website search
        res = self.client.get('/jobs?q=Principal+Systems+Architect')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Principal Systems Architect (Admin Posted)', res.data)

        # 7. Admin reviews application and updates status to 'Interview'
        with self.app.app_context():
            app_to_update = Application.query.first()
            target_app_id = app_to_update.id
            cand_id = app_to_update.candidate_id

        res = self.client.post(f'/admin/applications/{target_app_id}/status', data={
            'status': 'Interview'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'status updated to', res.data)

        # Verify DB updated
        with self.app.app_context():
            refreshed_app = db.session.get(Application, target_app_id)
            self.assertEqual(refreshed_app.status, 'Interview')

        # Logout Admin
        self.client.get('/auth/logout')

        # 8. Verify the updated status immediately shows on the candidate's dashboard and applications page
        with self.client.session_transaction() as sess:
            sess['user_id'] = cand_id
            sess['role'] = 'candidate'

        cand_dash_res = self.client.get('/candidate/dashboard')
        self.assertEqual(cand_dash_res.status_code, 200)
        self.assertIn(b'Interview', cand_dash_res.data)

        cand_apps_res = self.client.get('/candidate/applications')
        self.assertEqual(cand_apps_res.status_code, 200)
        self.assertIn(b'Interview', cand_apps_res.data)

        self.client.get('/auth/logout')

    def test_06_role_authorization_boundaries(self):
        """Verify role protection and security isolation."""
        # Unauthenticated user attempting protected endpoints
        res = self.client.get('/candidate/dashboard', follow_redirects=False)
        self.assertEqual(res.status_code, 302)
        self.assertIn('/auth/login', res.headers['Location'])

        res = self.client.get('/employer/dashboard', follow_redirects=False)
        self.assertEqual(res.status_code, 302)
        self.assertIn('/auth/login', res.headers['Location'])

        res = self.client.get('/admin/dashboard', follow_redirects=False)
        self.assertEqual(res.status_code, 302)
        self.assertIn('/auth/login', res.headers['Location'])

        # Candidate attempting Employer or Admin pages
        with self.app.app_context():
            cand = User.query.filter_by(role='candidate').first()
            cand_id = cand.id

        with self.client.session_transaction() as sess:
            sess['user_id'] = cand_id
            sess['role'] = 'candidate'

        res = self.client.get('/employer/dashboard', follow_redirects=False)
        self.assertEqual(res.status_code, 302)  # Redirected with flash message

        res = self.client.get('/admin/dashboard', follow_redirects=False)
        self.assertEqual(res.status_code, 302)

        # Employer attempting Admin pages
        with self.app.app_context():
            emp = User.query.filter_by(role='employer').first()
            emp_id = emp.id

        with self.client.session_transaction() as sess:
            sess['user_id'] = emp_id
            sess['role'] = 'employer'

        res = self.client.get('/admin/dashboard', follow_redirects=False)
        self.assertEqual(res.status_code, 302)

        # Employer A attempting to edit Employer B's job (must return 403 Forbidden)
        with self.app.app_context():
            other_job = Job.query.filter(Job.employer_id != emp_id).first()
            other_job_id = other_job.id

        res = self.client.get(f'/employer/jobs/{other_job_id}/edit')
        self.assertEqual(res.status_code, 403)

    def test_07_invalid_ids_and_duplicate_constraints(self):
        """Test 404 for invalid IDs and duplicate constraints."""
        # Invalid Job ID returns 404
        res = self.client.get('/jobs/999999')
        self.assertEqual(res.status_code, 404)

        # Invalid Company ID returns 404
        res = self.client.get('/companies/999999')
        self.assertEqual(res.status_code, 404)

        # Duplicate email registration is prevented
        res = self.client.post('/auth/register', data={
            'name': 'Duplicate User',
            'email': 'admin@jobportal.local',
            'password': 'Password@123',
            'confirm_password': 'Password@123',
            'role': 'candidate'
        }, follow_redirects=True)
        self.assertIn(b'already exists', res.data)

    def test_08_candidate_settings_and_password_change(self):
        """Test candidate settings: profile photo update/remove, contact info update, password change."""
        import uuid
        unique_email = f"settings.{uuid.uuid4().hex[:8]}@example.com"
        # Register a candidate for settings testing
        self.client.post('/auth/register', data={
            'name': 'Settings Tester',
            'email': unique_email,
            'password': 'InitialPassword123',
            'confirm_password': 'InitialPassword123',
            'role': 'candidate',
            'phone': '1112223333',
            'location': 'Seattle, WA'
        }, follow_redirects=True)

        with self.app.app_context():
            cand = User.query.filter_by(email=unique_email).first()
            cand_id = cand.id

        with self.client.session_transaction() as sess:
            sess['user_id'] = cand_id
            sess['role'] = 'candidate'

        # 1. Access Settings page
        res = self.client.get('/candidate/settings')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Account & Profile Settings', res.data)
        self.assertIn(b'Change Password', res.data)

        # 2. Update contact details
        res = self.client.post('/candidate/settings', data={
            'action': 'update_contact',
            'name': 'Settings Tester Updated',
            'phone': '+1 999 888 7777',
            'location': 'Bellevue, WA'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Account contact settings saved successfully', res.data)
        with self.app.app_context():
            updated_u = User.query.get(cand_id)
            self.assertEqual(updated_u.name, 'Settings Tester Updated')
            self.assertEqual(updated_u.phone, '+1 999 888 7777')
            self.assertEqual(updated_u.location, 'Bellevue, WA')

        # 3. Upload profile photo
        dummy_img = (io.BytesIO(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4"), 'avatar.png')
        res = self.client.post('/candidate/settings', data={
            'action': 'update_photo',
            'profile_photo': dummy_img
        }, content_type='multipart/form-data', follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Profile photo updated successfully', res.data)
        with self.app.app_context():
            updated_u = User.query.get(cand_id)
            self.assertIsNotNone(updated_u.profile_photo)

        # 4. Remove profile photo
        res = self.client.post('/candidate/settings', data={
            'action': 'remove_photo'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Profile photo has been removed', res.data)
        with self.app.app_context():
            updated_u = User.query.get(cand_id)
            self.assertIsNone(updated_u.profile_photo)

        # 5. Password change validations:
        # a) Incorrect current password
        res = self.client.post('/candidate/settings', data={
            'action': 'change_password',
            'current_password': 'WrongPassword123',
            'new_password': 'NewValidPassword123',
            'confirm_password': 'NewValidPassword123'
        }, follow_redirects=True)
        self.assertIn(b'Current password entered is incorrect', res.data)

        # b) Mismatched confirmation
        res = self.client.post('/candidate/settings', data={
            'action': 'change_password',
            'current_password': 'InitialPassword123',
            'new_password': 'NewValidPassword123',
            'confirm_password': 'DifferentPassword123'
        }, follow_redirects=True)
        self.assertIn(b'do not match', res.data)

        # c) Successful password change
        res = self.client.post('/candidate/settings', data={
            'action': 'change_password',
            'current_password': 'InitialPassword123',
            'new_password': 'BrandNewPassword@456',
            'confirm_password': 'BrandNewPassword@456'
        }, follow_redirects=True)
        self.assertIn(b'Your account password has been updated successfully', res.data)

        # Verify new password works
        with self.app.app_context():
            updated_u = User.query.get(cand_id)
            self.assertTrue(updated_u.check_password('BrandNewPassword@456'))
            self.assertFalse(updated_u.check_password('InitialPassword123'))

        self.client.get('/auth/logout')

    def test_09_notifications_lifecycle(self):
        """Test full notification flow: creation on application and status update, retrieval, mark as read."""
        import uuid
        unique_cand_email = f"notify.{uuid.uuid4().hex[:8]}@example.com"
        # Register candidate
        self.client.post('/auth/register', data={
            'name': 'Notify Candidate',
            'email': unique_cand_email,
            'password': 'Password@123',
            'confirm_password': 'Password@123',
            'role': 'candidate'
        }, follow_redirects=True)

        with self.app.app_context():
            cand = User.query.filter_by(email=unique_cand_email).first()
            cand_id = cand.id
            admin_user = User.query.filter_by(role='admin').first()
            admin_id = admin_user.id
            # Find an open job that this candidate hasn't applied to
            open_job = Job.query.filter_by(status='Open').first()
            job_id = open_job.id

        # 1. Candidate applies for an open job
        with self.client.session_transaction() as sess:
            sess['user_id'] = cand_id
            sess['role'] = 'candidate'

        dummy_resume = (io.BytesIO(b'%PDF-1.4 sample resume content'), 'resume.pdf')
        app_res = self.client.post(f'/jobs/{job_id}/apply', data={
            'applicant_name': 'Notify Candidate',
            'applicant_email': unique_cand_email,
            'applicant_phone': '+1 555-0101',
            'applicant_location': 'San Francisco, CA',
            'experience': '3 years',
            'qualification': 'B.S. Computer Science',
            'skills': 'Python, SQL',
            'cover_letter': 'Excited to apply for this role and test notifications.',
            'resume': dummy_resume
        }, content_type='multipart/form-data', follow_redirects=True)
        self.assertEqual(app_res.status_code, 200)

        # Candidate should have notification about submitting application
        with self.app.app_context():
            cand_notifs = Notification.query.filter_by(user_id=cand_id).all()
            self.assertGreaterEqual(len(cand_notifs), 1)
            sub_notif = next((n for n in cand_notifs if 'Application Submitted' in n.title), None)
            self.assertIsNotNone(sub_notif)
            self.assertFalse(sub_notif.is_read)
            notif_id = sub_notif.id

        # 2. Candidate checks notifications page
        res = self.client.get('/notifications/')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Notifications', res.data)
        self.assertIn(b'Application Submitted', res.data)

        # 3. Mark single notification as read
        mark_res = self.client.post(f'/notifications/{notif_id}/read', follow_redirects=True)
        self.assertEqual(mark_res.status_code, 200)
        with self.app.app_context():
            n = Notification.query.get(notif_id)
            self.assertTrue(n.is_read)

        # 4. Admin updates the application status with notes -> Candidate receives instant notification
        with self.app.app_context():
            app_record = Application.query.filter_by(job_id=job_id, candidate_id=cand_id).first()
            app_id = app_record.id

        with self.client.session_transaction() as sess:
            sess['user_id'] = admin_id
            sess['role'] = 'admin'

        status_res = self.client.post(f'/admin/applications/{app_id}/status', data={
            'status': 'Shortlisted',
            'admin_notes': 'Application reviewed and approved for technical evaluation.'
        }, follow_redirects=True)
        self.assertEqual(status_res.status_code, 200)

        # Verify candidate received status update notification
        with self.app.app_context():
            cand_notifs_after = Notification.query.filter_by(user_id=cand_id, is_read=False).all()
            self.assertGreaterEqual(len(cand_notifs_after), 1)
            found_status_notif = any('Shortlisted' in n.message or 'Status' in n.title for n in cand_notifs_after)
            self.assertTrue(found_status_notif)

        # 5. Candidate marks all as read
        with self.client.session_transaction() as sess:
            sess['user_id'] = cand_id
            sess['role'] = 'candidate'

        read_all_res = self.client.post('/notifications/read-all', follow_redirects=True)
        self.assertEqual(read_all_res.status_code, 200)
        with self.app.app_context():
            unread_count = Notification.query.filter_by(user_id=cand_id, is_read=False).count()
            self.assertEqual(unread_count, 0)

        self.client.get('/auth/logout')

    def test_10_admin_creates_user_and_candidate_settings_resume(self):
        """Test admin creating another candidate/user account and candidate settings resume management."""
        # 1. Admin login
        self.client.post('/auth/login', data={'email': 'admin@jobportal.local', 'password': 'AdminPassword@2026'}, follow_redirects=True)

        unique_email = f"admin.created.test.{uuid.uuid4().hex[:6]}@example.com"
        cand_resume_file = (io.BytesIO(b'%PDF-1.4 Admin Candidate Resume Content'), 'candidate_resume.pdf')
        cand_photo_file = (io.BytesIO(b'IMAGE_BYTES'), 'candidate_avatar.png')

        res = self.client.post('/admin/users/create', data={
            'role': 'candidate',
            'name': 'Admin Created Candidate',
            'email': unique_email,
            'password': 'SecureCandidate@123',
            'phone': '+1 555-888-9999',
            'location': 'Seattle, WA',
            'headline': 'Cloud Solutions Engineer',
            'skills': 'AWS, Docker, Python',
            'profile_photo': cand_photo_file,
            'resume': cand_resume_file
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'created successfully and saved in the database', res.data)

        # Verify DB
        with self.app.app_context():
            u = User.query.filter_by(email=unique_email).first()
            self.assertIsNotNone(u)
            self.assertEqual(u.role, 'candidate')
            self.assertIsNotNone(u.profile_photo)
            self.assertIsNotNone(u.candidate_profile.resume_path)
            cand_user_id = u.id

        self.client.get('/auth/logout')

        # 2. Login as the newly created candidate
        login_res = self.client.post('/auth/login', data={'email': unique_email, 'password': 'SecureCandidate@123'}, follow_redirects=True)
        self.assertEqual(login_res.status_code, 200)
        self.assertIn(b'Admin Created Candidate', login_res.data)

        # 3. Candidate updates resume from Settings page
        new_resume_file = (io.BytesIO(b'%PDF-1.4 Updated candidate resume from settings'), 'new_settings_resume.pdf')
        settings_res = self.client.post('/candidate/settings', data={
            'action': 'update_resume',
            'resume': new_resume_file
        }, follow_redirects=True)
        self.assertEqual(settings_res.status_code, 200)
        self.assertIn(b'Resume updated and saved to your profile successfully', settings_res.data)

        with self.app.app_context():
            u = db.session.get(User, cand_user_id)
            self.assertEqual(u.candidate_profile.resume_filename, 'new_settings_resume.pdf')

        self.client.get('/auth/logout')

    def test_11_candidate_only_public_registration_and_application_review(self):
        """Test that public registration enforces candidate-only role, application form strictly validates required details and resume, and admin updates status with notes reflecting to user."""
        import uuid
        cand_email = f"jobseeker.{uuid.uuid4().hex[:6]}@example.com"

        # 1. Verify public registration forces role='candidate' even if 'employer' role was requested
        reg_res = self.client.post('/auth/register', data={
            'name': 'Dedicated Job Seeker',
            'email': cand_email,
            'password': 'JobSeeker@123',
            'confirm_password': 'JobSeeker@123',
            'role': 'employer',  # Attempting employer role via public registration
            'phone': '+1 555-777-1234',
            'location': 'Austin, TX'
        }, follow_redirects=True)
        self.assertEqual(reg_res.status_code, 200)

        with self.app.app_context():
            u = User.query.filter_by(email=cand_email).first()
            self.assertIsNotNone(u)
            self.assertEqual(u.role, 'candidate')  # Must be forced to candidate!
            self.assertIsNotNone(u.candidate_profile)
            cand_id = u.id

        # 2. Login as candidate
        self.client.post('/auth/login', data={'email': cand_email, 'password': 'JobSeeker@123'}, follow_redirects=True)

        with self.app.app_context():
            open_job = Job.query.filter_by(status='Open').first()
            job_id = open_job.id

        # 3. Test form validation: Missing required fields (e.g. missing phone and qualification)
        val_fail_res = self.client.post(f'/jobs/{job_id}/apply', data={
            'applicant_name': 'Dedicated Job Seeker',
            'applicant_email': cand_email,
            'applicant_location': 'Austin, TX',
            'experience': '4 years',
            # missing qualification and skills
        }, follow_redirects=True)
        self.assertEqual(val_fail_res.status_code, 200)
        self.assertIn(b'Please complete all professional qualification fields', val_fail_res.data)

        # 4. Test resume validation: All fields filled, but no resume uploaded and no profile resume
        no_resume_res = self.client.post(f'/jobs/{job_id}/apply', data={
            'applicant_name': 'Dedicated Job Seeker',
            'applicant_email': cand_email,
            'applicant_phone': '+1 555-777-1234',
            'applicant_location': 'Austin, TX',
            'experience': '4 years',
            'qualification': 'Bachelor of Science',
            'skills': 'Python, Django, FastAPI',
            'cover_letter': 'Excited to submit my profile.'
        }, follow_redirects=True)
        self.assertEqual(no_resume_res.status_code, 200)
        self.assertIn(b'A Resume document is required to submit your application', no_resume_res.data)

        # 5. Successful application with valid form details + resume upload
        cv_file = (io.BytesIO(b'%PDF-1.4 Job Seeker Resume Data'), 'seeker_resume.pdf')
        apply_success_res = self.client.post(f'/jobs/{job_id}/apply', data={
            'applicant_name': 'Dedicated Job Seeker',
            'applicant_email': cand_email,
            'applicant_phone': '+1 555-777-1234',
            'applicant_location': 'Austin, TX',
            'experience': '4 years in Software Engineering',
            'qualification': 'Bachelor of Science in CS',
            'skills': 'Python, Flask, Docker, PostgreSQL',
            'cover_letter': 'I look forward to discussing how I can add value.',
            'resume': cv_file
        }, content_type='multipart/form-data', follow_redirects=True)
        self.assertEqual(apply_success_res.status_code, 200)
        self.assertIn(b'submitted successfully', apply_success_res.data)

        with self.app.app_context():
            app_record = Application.query.filter_by(job_id=job_id, candidate_id=cand_id).first()
            self.assertIsNotNone(app_record)
            self.assertEqual(app_record.status, 'Applied')
            self.assertEqual(app_record.applicant_name, 'Dedicated Job Seeker')
            self.assertEqual(app_record.applicant_phone, '+1 555-777-1234')
            self.assertEqual(app_record.qualification, 'Bachelor of Science in CS')
            self.assertEqual(app_record.skills, 'Python, Flask, Docker, PostgreSQL')
            self.assertIsNotNone(app_record.resume_path)
            app_id = app_record.id

        self.client.get('/auth/logout')

        # 6. Admin logs in and reviews application
        self.client.post('/auth/login', data={'email': 'admin@jobportal.local', 'password': 'AdminPassword@2026'}, follow_redirects=True)
        admin_apps_page = self.client.get('/admin/applications')
        self.assertEqual(admin_apps_page.status_code, 200)
        self.assertIn(b'Dedicated Job Seeker', admin_apps_page.data)

        # Admin updates status and adds recruiter review notes
        notes_text = 'Candidate meets all requirements. Scheduled for Round 1 technical interview.'
        admin_update_res = self.client.post(f'/admin/applications/{app_id}/status', data={
            'status': 'Interview',
            'admin_notes': notes_text
        }, follow_redirects=True)
        self.assertEqual(admin_update_res.status_code, 200)
        self.assertIn(b'status updated to', admin_update_res.data)

        with self.app.app_context():
            updated_app = db.session.get(Application, app_id)
            self.assertEqual(updated_app.status, 'Interview')
            self.assertEqual(updated_app.admin_notes, notes_text)

        self.client.get('/auth/logout')

        # 7. Candidate logs in, checks applications page, and verifies new status & recruiter notes
        self.client.post('/auth/login', data={'email': cand_email, 'password': 'JobSeeker@123'}, follow_redirects=True)
        cand_apps_res = self.client.get('/candidate/applications')
        self.assertEqual(cand_apps_res.status_code, 200)
        self.assertIn(b'Interview', cand_apps_res.data)
        self.assertIn(b'Candidate meets all requirements', cand_apps_res.data)

        self.client.get('/auth/logout')


if __name__ == '__main__':
    unittest.main()
