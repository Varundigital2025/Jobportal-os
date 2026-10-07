"""
Seed Script for JobPortal
Populates the database with realistic sample data:
- 1 Admin
- 3 Employers / Companies
- 5 Candidates with full profiles
- 12 Jobs across different categories, job types, and work modes
- Sample Applications with varied statuses
- Sample Saved Jobs
"""
from datetime import datetime, date, timedelta
from app import create_app
from extensions import db
from models.user import User
from models.candidate import CandidateProfile
from models.company import Company
from models.job import Job
from models.application import Application
from models.saved_job import SavedJob


def seed_database():
    app = create_app()
    with app.app_context():
        print("Clearing and rebuilding database for fresh seed...")
        db.drop_all()
        db.create_all()

        # 1. Admin
        admin = User(
            name="Platform Administrator",
            email="admin@jobportal.local",
            role="admin",
            phone="+1 (555) 019-2834",
            location="San Francisco, CA",
            is_active=True
        )
        admin.set_password("AdminPassword@2026")
        db.session.add(admin)

        # 2. Employers & Companies
        employer1 = User(
            name="Alex Mercer",
            email="alex.apex@example.com",
            role="employer",
            phone="+1 (555) 302-9182",
            location="Austin, TX",
            is_active=True
        )
        employer1.set_password("Employer@123")
        db.session.add(employer1)
        db.session.flush()

        company1 = Company(
            user_id=employer1.id,
            company_name="Apex Technologies",
            industry="Software & Engineering",
            company_size="51-200",
            website="https://apextech.example.com",
            location="Austin, TX",
            phone="+1 (555) 302-9182",
            description="Apex Technologies builds next-generation SaaS architectures and enterprise cloud management software used by thousands of companies worldwide."
        )
        db.session.add(company1)

        employer2 = User(
            name="Elena Rostova",
            email="elena.cloud@example.com",
            role="employer",
            phone="+1 (555) 839-4411",
            location="Seattle, WA",
            is_active=True
        )
        employer2.set_password("Employer@123")
        db.session.add(employer2)
        db.session.flush()

        company2 = Company(
            user_id=employer2.id,
            company_name="CloudSphere Global",
            industry="Cloud Computing & Infrastructure",
            company_size="201-500",
            website="https://cloudsphere.example.com",
            location="Seattle, WA",
            phone="+1 (555) 839-4411",
            description="CloudSphere Global is a high-growth cloud infrastructure platform providing automated multi-cloud scaling and serverless workflows."
        )
        db.session.add(company2)

        employer3 = User(
            name="Marcus Vance",
            email="marcus.pixel@example.com",
            role="employer",
            phone="+1 (555) 492-7722",
            location="New York, NY",
            is_active=True
        )
        employer3.set_password("Employer@123")
        db.session.add(employer3)
        db.session.flush()

        company3 = Company(
            user_id=employer3.id,
            company_name="PixelCraft Studios",
            industry="Product & Design",
            company_size="11-50",
            website="https://pixelcraft.example.com",
            location="New York, NY",
            phone="+1 (555) 492-7722",
            description="PixelCraft is a modern digital design studio creating responsive web and mobile interfaces, brand systems, and intuitive user experiences."
        )
        db.session.add(company3)
        db.session.flush()

        # 3. Candidates
        candidates_data = [
            {
                "name": "Devon Vance",
                "email": "devon.vance@example.com",
                "phone": "+1 (555) 718-2930",
                "location": "San Francisco, CA",
                "headline": "Senior Python & Backend Engineer",
                "bio": "Passionate backend engineer with 6+ years building scalable microservices, REST APIs, and event-driven architectures with Python, Flask, and PostgreSQL.",
                "skills": "Python, Flask, Django, PostgreSQL, Docker, Redis, REST APIs, Git",
                "experience": "6 years in high-throughput backend services and data pipelines.",
                "education": "B.S. in Computer Science - University of California, Berkeley",
                "qualification": "Bachelor of Science",
                "linkedin_url": "https://linkedin.com/in/devon-vance",
                "portfolio_url": "https://devonvance.dev"
            },
            {
                "name": "Sophia Chen",
                "email": "sophia.chen@example.com",
                "phone": "+1 (555) 882-1402",
                "location": "Austin, TX",
                "headline": "Full Stack Web Developer | React & Python",
                "bio": "Full stack developer with a focus on clean UI/UX, responsive layouts, and robust backend systems. Experienced in Python, JavaScript, and Tailwind CSS.",
                "skills": "JavaScript, Python, React, Tailwind CSS, HTML5, CSS3, SQLite, Node.js",
                "experience": "4 years building responsive web applications for B2B startups.",
                "education": "B.S. in Software Engineering - UT Austin",
                "qualification": "Bachelor of Science",
                "linkedin_url": "https://linkedin.com/in/sophia-chen",
                "portfolio_url": "https://sophiachen.me"
            },
            {
                "name": "Liam Miller",
                "email": "liam.miller@example.com",
                "phone": "+1 (555) 912-3044",
                "location": "Chicago, IL",
                "headline": "DevOps & Cloud Systems Engineer",
                "bio": "Specialist in CI/CD pipeline automation, container orchestration, Kubernetes, and AWS infrastructure management.",
                "skills": "AWS, Docker, Kubernetes, Terraform, Linux, CI/CD, Python, Bash",
                "experience": "5 years automating infrastructure and cloud deployments.",
                "education": "B.S. in Information Systems - University of Illinois",
                "qualification": "Bachelor of Science",
                "linkedin_url": "https://linkedin.com/in/liam-miller",
                "portfolio_url": "https://liammiller.cloud"
            },
            {
                "name": "Amina Zahra",
                "email": "amina.zahra@example.com",
                "phone": "+1 (555) 604-5519",
                "location": "New York, NY",
                "headline": "Lead UI/UX & Product Designer",
                "bio": "Designer driven by user empathy, human-computer interaction, design systems, and rapid prototyping in Figma.",
                "skills": "Figma, UI/UX Design, Wireframing, User Research, Prototyping, Design Systems, HTML/CSS",
                "experience": "5 years crafting web and mobile interfaces for fintech and healthtech products.",
                "education": "B.A. in Graphic Communication - NYU",
                "qualification": "Bachelor of Arts",
                "linkedin_url": "https://linkedin.com/in/amina-zahra",
                "portfolio_url": "https://aminazahra.design"
            },
            {
                "name": "Rahul Sharma",
                "email": "rahul.sharma@example.com",
                "phone": "+91 98765 43210",
                "location": "Hyderabad, India",
                "headline": "Data Scientist & Machine Learning Engineer",
                "bio": "Specializing in statistical analysis, predictive modeling, NLP pipelines, and data visualization using Python and SQL.",
                "skills": "Python, Machine Learning, SQL, Pandas, NumPy, Scikit-Learn, PyTorch, PowerBI",
                "experience": "3+ years delivering data-driven insights and ML models.",
                "education": "B.Tech in Computer Science - IIT Hyderabad",
                "qualification": "Bachelor of Technology",
                "linkedin_url": "https://linkedin.com/in/rahul-sharma-ml",
                "portfolio_url": "https://rahulsharma.ai"
            }
        ]

        candidate_users = []
        for cdata in candidates_data:
            cuser = User(
                name=cdata["name"],
                email=cdata["email"],
                role="candidate",
                phone=cdata["phone"],
                location=cdata["location"],
                is_active=True
            )
            cuser.set_password("Candidate@123")
            db.session.add(cuser)
            db.session.flush()

            profile = CandidateProfile(
                user_id=cuser.id,
                headline=cdata["headline"],
                bio=cdata["bio"],
                skills=cdata["skills"],
                experience=cdata["experience"],
                education=cdata["education"],
                qualification=cdata["qualification"],
                linkedin_url=cdata["linkedin_url"],
                portfolio_url=cdata["portfolio_url"],
                resume_filename="resume_sample.pdf",
                resume_path="sample_resume.pdf"
            )
            db.session.add(profile)
            candidate_users.append(cuser)

        # 4. Jobs
        sample_jobs = [
            {
                "employer": employer1,
                "company": company1,
                "title": "Senior Python Backend Developer",
                "category": "Software & Engineering",
                "location": "Austin, TX",
                "job_type": "Full Time",
                "work_mode": "Hybrid",
                "experience_level": "Senior Level",
                "salary_min": 120000,
                "salary_max": 160000,
                "skills": "Python, Flask, PostgreSQL, Docker, Redis",
                "description": "We are seeking an experienced Senior Python Backend Developer to join our core platform engineering team at Apex Technologies. You will architect and maintain high-performance web applications, optimize SQL queries, and design robust REST APIs.",
                "responsibilities": "• Architect, develop, and maintain clean, scalable Python web services.\n• Collaborate with front-end engineers to integrate user-facing elements.\n• Optimize database schemas and queries for maximum throughput and reliability.\n• Participate in code reviews and mentor junior developers.",
                "requirements": "• 5+ years of software development experience with Python.\n• Strong familiarity with Flask, Django, or FastAPI.\n• Deep knowledge of relational databases like PostgreSQL/SQLite.\n• Experience with containerization (Docker) and CI/CD pipelines.",
                "deadline": date.today() + timedelta(days=30),
                "status": "Open"
            },
            {
                "employer": employer1,
                "company": company1,
                "title": "Full Stack Engineer (Python + React)",
                "category": "Software & Engineering",
                "location": "Remote",
                "job_type": "Full Time",
                "work_mode": "Remote",
                "experience_level": "Mid Level",
                "salary_min": 95000,
                "salary_max": 130000,
                "skills": "Python, React, JavaScript, Tailwind CSS, SQL",
                "description": "Join our fast-paced product engineering team to build intuitive customer dashboards and reliable backend microservices.",
                "responsibilities": "• Build responsive frontend interfaces and robust backend APIs.\n• Collaborate with product managers and designers to translate requirements into elegant code.\n• Maintain unit tests and continuous integration workflows.",
                "requirements": "• 3+ years of full stack web development experience.\n• Proficiency in Python and modern JavaScript (React or Vanilla ES6).\n• Solid understanding of responsive CSS and RESTful API standards.",
                "deadline": date.today() + timedelta(days=25),
                "status": "Open"
            },
            {
                "employer": employer2,
                "company": company2,
                "title": "DevOps & Cloud Infrastructure Specialist",
                "category": "Software & Engineering",
                "location": "Seattle, WA",
                "job_type": "Full Time",
                "work_mode": "Hybrid",
                "experience_level": "Senior Level",
                "salary_min": 135000,
                "salary_max": 175000,
                "skills": "AWS, Kubernetes, Terraform, Docker, CI/CD",
                "description": "CloudSphere is looking for a DevOps Engineer to own our cloud deployments, monitor platform health, and ensure 99.99% system availability.",
                "responsibilities": "• Manage Kubernetes clusters across multiple AWS regions.\n• Write automated Terraform infrastructure-as-code scripts.\n• Improve deployment velocity with automated GitHub Actions workflows.",
                "requirements": "• 4+ years managing production cloud infrastructure on AWS or GCP.\n• In-depth knowledge of Kubernetes, Docker, and Linux internals.\n• Experience with monitoring tools like Prometheus and Grafana.",
                "deadline": date.today() + timedelta(days=40),
                "status": "Open"
            },
            {
                "employer": employer2,
                "company": company2,
                "title": "Machine Learning & AI Engineer",
                "category": "Data Science & AI",
                "location": "Seattle, WA",
                "job_type": "Full Time",
                "work_mode": "On-site",
                "experience_level": "Mid Level",
                "salary_min": 110000,
                "salary_max": 150000,
                "skills": "Python, PyTorch, Scikit-Learn, Pandas, NLP",
                "description": "Develop and deploy predictive analytics models and natural language processing pipelines to power automated customer insights.",
                "responsibilities": "• Train, evaluate, and deploy machine learning models to production.\n• Build data cleaning, feature engineering, and validation pipelines.\n• Work closely with software engineers to expose models via low-latency endpoints.",
                "requirements": "• Master's or Bachelor's degree in CS, Data Science, or related quantitative field.\n• Strong programming ability in Python and ML libraries.\n• Experience handling structured and unstructured datasets.",
                "deadline": date.today() + timedelta(days=20),
                "status": "Open"
            },
            {
                "employer": employer3,
                "company": company3,
                "title": "Lead UI/UX Product Designer",
                "category": "Product & Design",
                "location": "New York, NY",
                "job_type": "Full Time",
                "work_mode": "Hybrid",
                "experience_level": "Lead / Manager",
                "salary_min": 115000,
                "salary_max": 155000,
                "skills": "Figma, UI Design, Wireframing, Design Systems, User Research",
                "description": "PixelCraft Studios is looking for a visionary Lead UI/UX Product Designer to oversee client design systems and craft world-class web applications.",
                "responsibilities": "• Design intuitive user journeys, wireframes, and high-fidelity interactive prototypes in Figma.\n• Maintain and scale comprehensive design systems.\n• Conduct user interviews, usability tests, and design reviews.",
                "requirements": "• 5+ years of product design experience for web and mobile platforms.\n• Portfolio demonstrating strong typography, visual hierarchy, and interaction design.\n• Strong communication and client presentation skills.",
                "deadline": date.today() + timedelta(days=18),
                "status": "Open"
            },
            {
                "employer": employer3,
                "company": company3,
                "title": "Junior Frontend Web Designer",
                "category": "Product & Design",
                "location": "New York, NY",
                "job_type": "Part Time",
                "work_mode": "Remote",
                "experience_level": "Entry Level",
                "salary_min": 45000,
                "salary_max": 65000,
                "skills": "HTML5, CSS3, JavaScript, Tailwind CSS, Responsive Design",
                "description": "An exciting entry-level opportunity to convert creative Figma designs into clean, accessible, and responsive HTML/CSS/JS components.",
                "responsibilities": "• Build clean semantic HTML and modular CSS stylesheets.\n• Ensure cross-browser compatibility and mobile responsiveness.\n• Assist senior designers with asset preparation and design audits.",
                "requirements": "• Demonstrated knowledge of HTML5, CSS3, and modern CSS frameworks.\n• Eagerness to learn and attention to visual detail.\n• Basic knowledge of Git version control.",
                "deadline": date.today() + timedelta(days=15),
                "status": "Open"
            },
            {
                "employer": employer1,
                "company": company1,
                "title": "Product Growth Marketing Manager",
                "category": "Marketing & Content",
                "location": "Austin, TX",
                "job_type": "Full Time",
                "work_mode": "Remote",
                "experience_level": "Mid Level",
                "salary_min": 85000,
                "salary_max": 115000,
                "skills": "SEO, Google Analytics, Content Strategy, Email Campaigns",
                "description": "Lead digital growth marketing campaigns, optimize onboarding funnels, and manage content strategy to drive user acquisition.",
                "responsibilities": "• Design and execute inbound growth marketing experiments.\n• Analyze conversion metrics and conduct A/B testing on landing pages.\n• Collaborate with design and sales teams to build marketing assets.",
                "requirements": "• 3+ years in growth marketing or B2B SaaS marketing.\n• Hands-on experience with analytics tools, SEO, and email workflows.",
                "deadline": date.today() + timedelta(days=22),
                "status": "Open"
            },
            {
                "employer": employer2,
                "company": company2,
                "title": "Technical Customer Success Specialist",
                "category": "Customer Success & Support",
                "location": "Remote",
                "job_type": "Full Time",
                "work_mode": "Remote",
                "experience_level": "Entry Level",
                "salary_min": 55000,
                "salary_max": 75000,
                "skills": "Customer Support, Troubleshooting, API Integration, Zendesk",
                "description": "Help developers and enterprise customers onboard successfully onto CloudSphere, troubleshoot API integrations, and resolve technical tickets.",
                "responsibilities": "• Provide prompt and empathetic technical support via ticketing and live chat.\n• Create self-service documentation and knowledge base guides.\n• Escalate recurring bugs to engineering team with reproducible steps.",
                "requirements": "• Outstanding written English communication skills.\n• Basic technical background (familiarity with APIs, HTTP codes, JSON).\n• Customer-first mindset and high problem-solving drive.",
                "deadline": date.today() + timedelta(days=35),
                "status": "Open"
            },
            {
                "employer": employer1,
                "company": company1,
                "title": "Junior Python QA & Automation Tester",
                "category": "Software & Engineering",
                "location": "Austin, TX",
                "job_type": "Contract",
                "work_mode": "On-site",
                "experience_level": "Entry Level",
                "salary_min": 60000,
                "salary_max": 80000,
                "skills": "Python, PyTest, Selenium, API Testing, Git",
                "description": "Write automated test scripts, build regression suites, and verify endpoints for our core platform release cycles.",
                "responsibilities": "• Write and execute automated test cases using Python and PyTest.\n• Validate REST API payloads, error handling, and performance.\n• Document defect reports in Jira with clear reproduction steps.",
                "requirements": "• Knowledge of Python and basic testing fundamentals.\n• Understanding of web protocols and testing concepts.\n• High attention to detail.",
                "deadline": date.today() + timedelta(days=12),
                "status": "Open"
            },
            {
                "employer": employer2,
                "company": company2,
                "title": "Senior Solutions Architect",
                "category": "Sales & Business Development",
                "location": "Seattle, WA",
                "job_type": "Full Time",
                "work_mode": "Hybrid",
                "experience_level": "Senior Level",
                "salary_min": 140000,
                "salary_max": 185000,
                "skills": "Cloud Architecture, Client Demos, Enterprise Sales, AWS",
                "description": "Partner with enterprise sales executives to lead technical pre-sales discussions, architectural workshops, and custom proofs of concept.",
                "responsibilities": "• Act as technical trusted advisor for prospective enterprise accounts.\n• Design high-availability cloud architecture diagrams for client RFP requirements.\n• Deliver compelling technical product presentations.",
                "requirements": "• 5+ years experience in customer-facing technical sales or architecture roles.\n• In-depth cloud understanding (AWS, Azure, or GCP certified preferred).\n• Excellent verbal presentation and client engagement skills.",
                "deadline": date.today() + timedelta(days=28),
                "status": "Open"
            },
            {
                "employer": employer3,
                "company": company3,
                "title": "Freelance Brand & Graphic Designer",
                "category": "Product & Design",
                "location": "Remote",
                "job_type": "Freelance",
                "work_mode": "Remote",
                "experience_level": "Mid Level",
                "salary_min": 40,
                "salary_max": 75,
                "salary_currency": "$/hr",
                "skills": "Illustrator, Photoshop, Brand Identity, Vector Graphics",
                "description": "Join our network of freelance creators for ongoing brand visual identity projects, pitch decks, and digital media campaigns.",
                "responsibilities": "• Create custom illustrations, icon packs, and vector assets.\n• Adhere to brand identity standards across deliverables.\n• Iterate quickly based on creative director and client feedback.",
                "requirements": "• Strong design portfolio demonstrating branding and graphic art.\n• Expert command of Adobe Creative Cloud.\n• Reliable communication and ability to meet agreed project deadlines.",
                "deadline": date.today() + timedelta(days=10),
                "status": "Open"
            },
            {
                "employer": employer1,
                "company": company1,
                "title": "Database Administrator (SQLite & PostgreSQL)",
                "category": "Software & Engineering",
                "location": "Austin, TX",
                "job_type": "Full Time",
                "work_mode": "On-site",
                "experience_level": "Senior Level",
                "salary_min": 110000,
                "salary_max": 145000,
                "skills": "PostgreSQL, SQLite, Indexing, Query Optimization, Backup Systems",
                "description": "Manage database performance, schema migrations, backup strategies, and query tuning across production clusters.",
                "responsibilities": "• Monitor database query execution plans and optimize slow indexes.\n• Maintain automated backup, replication, and disaster recovery plans.\n• Advise software developers on optimal schema architectures.",
                "requirements": "• 4+ years dedicated database management experience.\n• Strong SQL tuning expertise.",
                "deadline": date.today() - timedelta(days=5),
                "status": "Closed"  # One closed job to demonstrate closed state!
            }
        ]

        created_jobs = []
        for jdata in sample_jobs:
            job = Job(
                employer_id=jdata["employer"].id,
                company_id=jdata["company"].id,
                title=jdata["title"],
                category=jdata["category"],
                location=jdata["location"],
                job_type=jdata["job_type"],
                work_mode=jdata["work_mode"],
                experience_level=jdata["experience_level"],
                salary_min=jdata["salary_min"],
                salary_max=jdata["salary_max"],
                salary_currency=jdata.get("salary_currency", "$"),
                skills=jdata["skills"],
                description=jdata["description"],
                responsibilities=jdata["responsibilities"],
                requirements=jdata["requirements"],
                deadline=jdata["deadline"],
                status=jdata["status"]
            )
            db.session.add(job)
            created_jobs.append(job)

        db.session.flush()

        # 5. Sample Applications
        # Devon applies to Senior Python Backend Developer (Shortlisted)
        app1 = Application(
            job_id=created_jobs[0].id,
            candidate_id=candidate_users[0].id,
            resume_path="sample_resume.pdf",
            cover_letter="I am very excited about Apex Technologies' focus on clean SaaS architectures. With 6+ years of Python and Flask experience, I have built similar systems and would love to contribute.",
            status="Shortlisted"
        )
        db.session.add(app1)

        # Sophia applies to Full Stack Engineer (Under Review)
        app2 = Application(
            job_id=created_jobs[1].id,
            candidate_id=candidate_users[1].id,
            resume_path="sample_resume.pdf",
            cover_letter="I love building end-to-end user features with React and Python backends. I look forward to speaking with the team.",
            status="Under Review"
        )
        db.session.add(app2)

        # Liam applies to DevOps & Cloud Infrastructure (Interview)
        app3 = Application(
            job_id=created_jobs[2].id,
            candidate_id=candidate_users[2].id,
            resume_path="sample_resume.pdf",
            cover_letter="As an AWS and Kubernetes specialist, I am confident in managing CloudSphere's multi-cloud deployments seamlessly.",
            status="Interview"
        )
        db.session.add(app3)

        # Amina applies to Lead UI/UX Product Designer (Applied)
        app4 = Application(
            job_id=created_jobs[4].id,
            candidate_id=candidate_users[3].id,
            resume_path="sample_resume.pdf",
            cover_letter="PixelCraft's design ethos matches my passion for accessible, refined design systems. Please find my portfolio linked in my profile.",
            status="Applied"
        )
        db.session.add(app4)

        # Rahul applies to Machine Learning & AI Engineer (Under Review)
        app5 = Application(
            job_id=created_jobs[3].id,
            candidate_id=candidate_users[4].id,
            resume_path="sample_resume.pdf",
            cover_letter="I have developed multiple NLP and predictive machine learning models in production, and would love to apply these skills at CloudSphere.",
            status="Under Review"
        )
        db.session.add(app5)

        # 6. Sample Saved Jobs
        db.session.add(SavedJob(candidate_id=candidate_users[0].id, job_id=created_jobs[1].id))
        db.session.add(SavedJob(candidate_id=candidate_users[0].id, job_id=created_jobs[2].id))
        db.session.add(SavedJob(candidate_id=candidate_users[1].id, job_id=created_jobs[0].id))
        db.session.add(SavedJob(candidate_id=candidate_users[3].id, job_id=created_jobs[5].id))

        db.session.commit()
        print("\n" + "="*60)
        print("SEEDING COMPLETED SUCCESSFULLY!")
        print("="*60)
        print("ACCOUNTS CREATED FOR TESTING:")
        print("1. Admin Account:")
        print("   Email:    admin@jobportal.local")
        print("   Password: AdminPassword@2026")
        print("\n2. Employer Accounts:")
        print("   Email:    alex.apex@example.com (Apex Technologies)")
        print("   Email:    elena.cloud@example.com (CloudSphere Global)")
        print("   Email:    marcus.pixel@example.com (PixelCraft Studios)")
        print("   Password: Employer@123")
        print("\n3. Candidate Accounts:")
        print("   Email:    devon.vance@example.com (Senior Python)")
        print("   Email:    sophia.chen@example.com (Full Stack)")
        print("   Email:    liam.miller@example.com (DevOps)")
        print("   Email:    amina.zahra@example.com (UI/UX Designer)")
        print("   Email:    rahul.sharma@example.com (ML Engineer)")
        print("   Password: Candidate@123")
        print(f"\nTotal Jobs Created: {len(created_jobs)}")
        print(f"Total Applications Created: 5")
        print("="*60 + "\n")


if __name__ == '__main__':
    seed_database()
