from sqlalchemy import or_, and_, desc, func
from extensions import db
from models.job import Job
from models.company import Company
from models.user import User


def get_popular_categories(limit=8):
    """Returns top job categories with counts of open jobs."""
    results = db.session.query(
        Job.category,
        func.count(Job.id).label('job_count')
    ).filter(Job.status == 'Open')\
     .group_by(Job.category)\
     .order_by(desc('job_count'))\
     .limit(limit)\
     .all()

    # Fallback default categories if empty
    default_categories = [
        ('Software & Engineering', 0),
        ('Data Science & AI', 0),
        ('Product & Design', 0),
        ('Marketing & Content', 0),
        ('Sales & Business Development', 0),
        ('Finance & Accounting', 0),
        ('Customer Success & Support', 0),
        ('Human Resources', 0)
    ]
    if not results:
        return default_categories
    return results


def get_featured_jobs(limit=6):
    """Returns recently posted open jobs for homepage."""
    return Job.query.filter_by(status='Open')\
        .order_by(Job.created_at.desc())\
        .limit(limit)\
        .all()


def get_top_companies(limit=6):
    """Returns companies that currently have open jobs."""
    return Company.query.join(Job, Company.id == Job.company_id)\
        .filter(Job.status == 'Open')\
        .group_by(Company.id)\
        .order_by(desc(func.count(Job.id)))\
        .limit(limit)\
        .all()


def search_jobs(keyword=None, location=None, category=None, job_type=None,
                work_mode=None, experience_level=None, min_salary=None,
                sort_by='newest', page=1, per_page=9):
    """
    Search and filter jobs with dynamic query builder and pagination.
    """
    query = Job.query.join(Company, Job.company_id == Company.id, isouter=True)
    query = query.filter(Job.status == 'Open')

    # Keyword filter across title, description, skills, company name
    if keyword and keyword.strip():
        term = f"%{keyword.strip()}%"
        query = query.filter(
            or_(
                Job.title.ilike(term),
                Job.description.ilike(term),
                Job.skills.ilike(term),
                Company.company_name.ilike(term)
            )
        )

    # Location filter
    if location and location.strip():
        term = f"%{location.strip()}%"
        query = query.filter(Job.location.ilike(term))

    # Category filter
    if category and category.strip() and category != 'All':
        query = query.filter(Job.category == category.strip())

    # Job type filter
    if job_type and job_type.strip() and job_type != 'All':
        query = query.filter(Job.job_type == job_type.strip())

    # Work mode filter
    if work_mode and work_mode.strip() and work_mode != 'All':
        query = query.filter(Job.work_mode == work_mode.strip())

    # Experience level filter
    if experience_level and experience_level.strip() and experience_level != 'All':
        query = query.filter(Job.experience_level == experience_level.strip())

    # Minimum salary filter
    if min_salary:
        try:
            val = int(min_salary)
            query = query.filter(
                or_(
                    Job.salary_min >= val,
                    Job.salary_max >= val
                )
            )
        except (ValueError, TypeError):
            pass

    # Sorting
    if sort_by == 'salary':
        query = query.order_by(desc(Job.salary_max), desc(Job.salary_min))
    elif sort_by == 'title':
        query = query.order_by(Job.title.asc())
    elif sort_by == 'oldest':
        query = query.order_by(Job.created_at.asc())
    else:  # newest default
        query = query.order_by(Job.created_at.desc())

    return query.paginate(page=page, per_page=per_page, error_out=False)
