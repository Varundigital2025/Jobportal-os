"""
Database Initialization Script for JobPortal
Creates SQLite tables and an initial administrator account if one does not exist.
"""
from app import create_app
from extensions import db
from models.user import User


def init_database():
    app = create_app()
    with app.app_context():
        print("Creating all database tables...")
        db.create_all()

        # Check if admin exists
        admin = User.query.filter_by(role='admin').first()
        if not admin:
            admin_email = "admin@jobportal.local"
            admin_password = "AdminPassword@2026"
            admin = User(
                name="Platform Administrator",
                email=admin_email,
                role="admin",
                phone="+1 (555) 019-2834",
                location="San Francisco, CA",
                is_active=True
            )
            admin.set_password(admin_password)
            db.session.add(admin)
            db.session.commit()
            print("="*60)
            print("INITIAL ADMINISTRATOR CREATED:")
            print(f"  Email:    {admin_email}")
            print(f"  Password: {admin_password}")
            print("  Please log in and update credentials in production.")
            print("="*60)
        else:
            print(f"Existing administrator account found: {admin.email}")

        print("Database initialization complete.")


if __name__ == '__main__':
    init_database()
