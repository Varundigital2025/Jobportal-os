# JobPortal — Full-Stack Python & Flask Job Application Platform

A complete, production-structured, local Job Portal web application connecting **Job Seekers / Candidates**, **Employers / Recruiters**, and **Platform Administrators**.

Built from scratch using **Python 3**, **Flask**, **SQLite**, **SQLAlchemy**, **HTML5/CSS3/JavaScript**, **Tailwind CSS**, and **Werkzeug**.

> **No XAMPP or Apache required.** Runs natively and locally on Windows with `python app.py`.

---

## 🚀 Key Features

### 👤 For Candidates / Job Seekers
* **Registration & Secure Login**: Werkzeug salted password hashing and role validation.
* **Candidate Profile & Strength Bar**: Manage headline, bio, skills, work experience, education, qualification, LinkedIn, and portfolio with real-time profile completion scoring.
* **Resume & Photo Uploads**: Upload and download PDF/DOC/DOCX resumes and avatar photos stored securely with randomized UUID filenames.
* **Multi-Criteria Job Search & Filters**: Search by keyword (title, description, skills, company), location, category, job type, work mode, experience level, and minimum salary.
* **Instant Application Workflow**: Submit applications with personalized cover letters; automatically attaches your default resume or accepts custom resume uploads.
* **Duplicate Prevention**: System guarantees candidates cannot submit duplicate applications for the same role.
* **Real-time Status Tracking**: Monitor your application timeline (`Applied`, `Under Review`, `Shortlisted`, `Interview`, `Rejected`, `Selected`).
* **Saved Jobs / Bookmarks**: Save positions with instant bookmarking to review or apply later.

### 🏢 For Employers / Recruiters
* **Employer Authentication & Company Profiles**: Create and edit company profile with logo, description, industry, company size, website, location, and phone.
* **Job Posting & Management**: Create, edit, toggle (`Open` / `Closed`), or delete jobs. Automatic company association.
* **Applicant Review Dashboard**: View all candidates who applied to your postings.
* **Candidate Profile Inspection**: Inspect candidate bio, skills, education, and cover letters via interactive modals.
* **Resume Access**: Securely download applicant resumes with access control.
* **Status Updates**: Advance applicants through the pipeline (`Applied` &rarr; `Under Review` &rarr; `Shortlisted` &rarr; `Interview` &rarr; `Selected` / `Rejected`). Candidate dashboards reflect updates immediately.
* **Multi-Tenant Protection**: Strict authorization ensuring Employer A cannot modify Employer B's jobs or access other employers' applicant records.

### 🛡️ For Administrators
* **Create & Publish Jobs**: Administrators can post new jobs directly (`/admin/jobs/create`), optionally assigning the role to any registered employer/company or posting as official JobPortal administration roles. Created jobs immediately appear across public searches, categories, and the homepage.
* **Review & Update Applications**: Comprehensive review panel for candidate submissions (`/admin/applications`) including candidate contact info, full profile background, cover letter, and resume downloads. Admins can update the application status (`Applied`, `Under Review`, `Shortlisted`, `Interview`, `Rejected`, `Selected`), which immediately updates on candidate dashboards and tracking pages.
* **Analytics Dashboard**: Real-time platform statistics (Total Users, Candidates, Employers, Total Jobs, Active Jobs, Total Applications) with visual Chart.js graphs.
* **User Governance**: Search users, filter by role, activate or deactivate accounts, or delete accounts (safely preventing deletion of the last admin).
* **Job Moderation**: Audit all platform jobs, close inappropriate positions, or delete violating records.

---

## 📁 Project Structure

```text
jobportalerp/
│
├── app.py                     # Flask application factory, context processors & server runner
├── config.py                  # Environment-driven configuration (Database, Uploads, Pagination)
├── extensions.py              # Central SQLAlchemy instance
├── requirements.txt           # Project Python dependencies
├── .env.example               # Template environment configuration
├── .gitignore                 # Git ignore rules for venv, database, and uploads
├── init_db.py                 # Database table initialization & default admin creation
├── seed.py                    # Comprehensive demo seeder (Employers, Candidates, Jobs, Applications)
├── database.db                # SQLite database (auto-generated)
├── README.md                  # Comprehensive platform documentation
│
├── models/                    # SQLAlchemy database models
│   ├── __init__.py            # Model registry
│   ├── user.py                # User model with Werkzeug password hashing
│   ├── candidate.py           # CandidateProfile model & profile completion scoring
│   ├── company.py             # Company model with active job relationships
│   ├── job.py                 # Job model with multi-field search helpers
│   ├── application.py         # Application model with status badges
│   └── saved_job.py           # SavedJob model with duplicate protection
│
├── routes/                    # Flask modular blueprints
│   ├── __init__.py
│   ├── auth.py                # Registration, login, logout, password recovery
│   ├── candidate.py           # Candidate dashboard, profile, resume, applications, saved jobs
│   ├── employer.py            # Employer dashboard, company profile, jobs CRUD, applicant reviews
│   ├── jobs.py                # Public job listings, multi-filter search, details, apply, save
│   └── admin.py               # Administrator dashboard, user management, moderation
│
├── services/                  # Business logic & abstraction services
│   ├── __init__.py
│   ├── auth_service.py        # Role decorators (@candidate_required, @employer_required, @admin_required)
│   ├── file_service.py        # Secure UUID file upload handlers (resumes, photos, logos)
│   ├── job_service.py         # Search query builder, filters, and category aggregations
│   └── application_service.py # Application submission & bookmark toggles
│
├── templates/                 # Jinja2 HTML templates
│   ├── base.html              # Core layout, role-aware navigation, flash toasts, footer
│   ├── home.html              # Modern homepage with hero search, categories, featured jobs
│   ├── jobs.html              # Search and multi-filter listing page with pagination
│   ├── job-details.html       # Job description, specifications, and application modal
│   ├── about.html             # Platform mission and architecture overview
│   ├── companies.html         # Hiring companies directory
│   ├── company-details.html   # Company profile and its open positions
│   │
│   ├── components/            # Reusable Jinja components
│   │   ├── job_card.html      # Reusable responsive job card
│   │   └── pagination.html    # Query-preserving pagination component
│   │
│   ├── auth/
│   │   ├── login.html         # Login page with demo credentials
│   │   ├── register.html      # Role selector (Job Seeker / Employer) registration
│   │   └── forgot-password.html
│   │
│   ├── candidate/
│   │   ├── dashboard.html     # Candidate metrics, progress bar, and recent activity
│   │   ├── profile.html       # Full candidate profile editor
│   │   ├── resume.html        # Resume upload, replace, and download
│   │   ├── applications.html  # Status tracking table with cover letter inspection
│   │   └── saved-jobs.html    # Bookmarked jobs
│   │
│   ├── employer/
│   │   ├── dashboard.html     # Employer recruitment analytics and recent jobs
│   │   ├── company-profile.html # Company profile editor and logo upload
│   │   ├── jobs.html          # Employer's jobs table with status toggles
│   │   ├── create-job.html    # Professional job posting form
│   │   ├── edit-job.html      # Job editor
│   │   └── applicants.html    # Candidate review table with status update dropdown
│   │
│   ├── admin/
│   │   ├── dashboard.html     # Admin analytics with Chart.js distribution charts
│   │   ├── users.html         # User search, activate/deactivate, delete
│   │   ├── employers.html     # Company directory audit
│   │   ├── jobs.html          # Platform job moderation and status changes
│   │   └── applications.html  # Application review log
│   │
│   └── errors/
│       ├── 404.html           # Page Not Found
│       ├── 403.html           # Access Denied
│       └── 500.html           # Server Error
│
├── static/
│   ├── css/
│   │   └── style.css          # CSS design tokens (:root variables, badges, buttons, cards)
│   ├── js/
│   │   └── app.js             # Mobile menu, modals, flash auto-dismiss, AJAX bookmarking
│   └── images/
│
└── uploads/                   # Secure uploads directory
    ├── resumes/               # Candidate resumes (PDF, DOC, DOCX)
    ├── profile_photos/        # Candidate avatars
    └── company_logos/         # Employer logos
```

---

## 🛠️ Requirements

* **Operating System**: Windows 10/11 (or macOS / Linux)
* **Python**: 3.10+ (tested on Python 3.12)
* **Package Manager**: `pip` (or `uv`)

---

## ⚡ Installation & Setup

### 1. Open Terminal in the Project Directory
```powershell
cd D:\jobportalerp
```

### 2. Create and Activate Virtual Environment
```powershell
python -m venv venv
.\venv\Scripts\activate
```

### 3. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 4. Initialize Database
Creates database tables and default administrator account:
```powershell
python init_db.py
```

### 5. (Optional) Seed Sample Data
Populates the database with 1 admin, 3 employers, 5 candidates, 12 rich jobs, and sample applications:
```powershell
python seed.py
```

### 6. Run the Application
```powershell
python app.py
```

### 7. Access in Browser
Open:
```text
http://127.0.0.1:5000
```

---

## 🔑 Pre-Configured Demo Accounts (From `seed.py`)

| Role | Email | Password | Details |
| :--- | :--- | :--- | :--- |
| **Administrator** | `admin@jobportal.local` | `AdminPassword@2026` | Full system access & moderation |
| **Employer 1** | `alex.apex@example.com` | `Employer@123` | Apex Technologies (SaaS) |
| **Employer 2** | `elena.cloud@example.com` | `Employer@123` | CloudSphere Global (Cloud) |
| **Employer 3** | `marcus.pixel@example.com` | `Employer@123` | PixelCraft Studios (Design) |
| **Candidate 1** | `devon.vance@example.com` | `Candidate@123` | Senior Python Developer |
| **Candidate 2** | `sophia.chen@example.com` | `Candidate@123` | Full Stack Developer |
| **Candidate 3** | `liam.miller@example.com` | `Candidate@123` | DevOps & Cloud Engineer |
| **Candidate 4** | `amina.zahra@example.com` | `Candidate@123` | Lead UI/UX Product Designer |
| **Candidate 5** | `rahul.sharma@example.com` | `Candidate@123` | Data Scientist & ML Specialist |

---

## 🔒 Security Best Practices Implemented

1. **Password Hashing**: Passwords hashed using Werkzeug (`generate_password_hash` / `check_password_hash`). Plain-text passwords are never saved.
2. **Role-Based Authorization**: Protected endpoints using `@login_required`, `@candidate_required`, `@employer_required`, and `@admin_required`.
3. **Multi-Tenant Isolation**: Employers can only edit/delete their own jobs and view applicants for their own jobs.
4. **Administrative Protection**: Safety guard preventing deletion of the last remaining admin account.
5. **Secure Upload Handling**: Files validated for extension and MIME type. Safe filenames generated using 12-character hex UUIDs to eliminate path traversal and collisions.
6. **File Access Control**: Resume downloads are protected routes; only the candidate, the hiring employer of the applied job, or admins can download applicant resumes.
7. **SQL Injection Defense**: All database operations execute through SQLAlchemy ORM parameterized queries.

---

## 🔄 Database Migration Readiness (PostgreSQL / MySQL)

The application utilizes SQLAlchemy models and standard relational constraints. To migrate from SQLite to PostgreSQL or MySQL:
1. Set the `DATABASE_URL` environment variable in `.env`:
   ```env
   DATABASE_URL=postgresql://user:password@localhost:5432/jobportal_db
   ```
2. Install the appropriate database driver:
   ```powershell
   pip install psycopg2-binary
   ```
   No modifications to Python application logic or routes are required.

---

## 🤖 Future AI Integration Architecture

The architecture is prepared for future AI feature services in `services/`:
* `services/ai_matching_service.py`: Computes cosine similarity between Candidate skills/bio embeddings and Job requirements.
* `services/ai_resume_parser.py`: Extracts structured experience and skills from uploaded PDF resumes.
* `services/ai_job_copilot.py`: Generates job descriptions, responsibilities, and interview questions for employers.
