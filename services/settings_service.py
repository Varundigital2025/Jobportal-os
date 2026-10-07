import secrets
from extensions import db
from models.system_setting import SystemSetting

DEFAULT_SETTINGS = {
    # Admin Portal Identity (shows different from the main website)
    'admin_portal_name': 'JobPortal Admin Suite',
    'admin_portal_tagline': 'Executive ERP & Operations Console',
    'admin_portal_logo': '',
    'admin_theme': 'slate',  # 'slate', 'dark', 'indigo', 'rose', 'emerald'
    'admin_badge_text': 'SuperAdmin Console',

    # Public Website Identity & Branding
    'site_name': 'JobPortal',
    'site_tagline': 'Connect With Top Careers & Talent',
    'site_logo': '',
    'site_favicon': '',
    'contact_email': 'support@jobportal.local',
    'contact_phone': '+1 (555) 019-2834',
    'company_address': 'San Francisco, CA, USA',
    'footer_text': 'Connecting talented job seekers with industry-leading employers. Explore career opportunities, apply seamlessly, and build your future.',
    'copyright_text': '© 2026 JobPortal Application. Running with Python & Flask.',
    'social_linkedin': 'https://linkedin.com',
    'social_github': 'https://github.com',
    'social_twitter': 'https://twitter.com',

    # Future ERP / External Integrations
    'webhook_url': '',
    'webhook_secret': '',
    'api_key': '',
    'integration_mode': 'standalone',  # 'standalone', 'erp_sync', 'api_bridge'
    'allow_candidate_registration': 'true',
    'allow_employer_registration': 'true',
    'maintenance_mode': 'false',
    'custom_css': '',
    'custom_header_script': '',
}

SETTING_GROUPS = {
    'admin_portal_name': 'admin_portal',
    'admin_portal_tagline': 'admin_portal',
    'admin_portal_logo': 'admin_portal',
    'admin_theme': 'admin_portal',
    'admin_badge_text': 'admin_portal',

    'site_name': 'general',
    'site_tagline': 'general',
    'site_logo': 'general',
    'site_favicon': 'general',
    'contact_email': 'general',
    'contact_phone': 'general',
    'company_address': 'general',
    'footer_text': 'general',
    'copyright_text': 'general',
    'social_linkedin': 'general',
    'social_github': 'general',
    'social_twitter': 'general',

    'webhook_url': 'integration',
    'webhook_secret': 'integration',
    'api_key': 'integration',
    'integration_mode': 'integration',
    'allow_candidate_registration': 'integration',
    'allow_employer_registration': 'integration',
    'maintenance_mode': 'integration',
    'custom_css': 'integration',
    'custom_header_script': 'integration',
}


import os


def is_valid_branding_file(filename):
    """Verifies that a branding image file exists on disk and is not a corrupted dummy file."""
    if not filename or not isinstance(filename, str):
        return False
    from config import Config
    path = os.path.join(Config.BRANDING_FOLDER, filename)
    return os.path.exists(path) and os.path.getsize(path) > 100


def get_all_settings():
    """
    Returns all configuration values as a dictionary, falling back to defaults.
    Ensures templates and services always have reliable access to settings.
    """
    settings = dict(DEFAULT_SETTINGS)
    try:
        stored = SystemSetting.query.all()
        for s in stored:
            settings[s.key] = s.value if s.value is not None else ''

        # Smart logo resilience: ensure valid logo files are served across public & admin
        site_logo = settings.get('site_logo', '')
        admin_logo = settings.get('admin_portal_logo', '')
        site_valid = is_valid_branding_file(site_logo)
        admin_valid = is_valid_branding_file(admin_logo)

        if not site_valid and admin_valid:
            settings['site_logo'] = admin_logo
        elif not site_valid:
            settings['site_logo'] = ''

        if not admin_valid and site_valid:
            settings['admin_portal_logo'] = site_logo
        elif not admin_valid:
            settings['admin_portal_logo'] = ''

    except Exception:
        # If database table is not yet initialized or during migrations, return defaults
        pass
    return settings


def get_setting(key, default=None):
    """
    Retrieves a single setting value with smart fallback for branding assets.
    """
    try:
        setting = SystemSetting.query.filter_by(key=key).first()
        if setting and setting.value is not None:
            val = setting.value
            if key in ['site_logo', 'admin_portal_logo']:
                if not is_valid_branding_file(val):
                    other_key = 'admin_portal_logo' if key == 'site_logo' else 'site_logo'
                    other_setting = SystemSetting.query.filter_by(key=other_key).first()
                    if other_setting and other_setting.value and is_valid_branding_file(other_setting.value):
                        return other_setting.value
                    return default or ''
            return val
    except Exception:
        pass
    return DEFAULT_SETTINGS.get(key, default)


def set_setting(key, value, group=None, description=None):
    """
    Sets or creates a single setting.
    """
    try:
        setting = SystemSetting.query.filter_by(key=key).first()
        if not setting:
            setting = SystemSetting(
                key=key,
                value=value,
                group=group or SETTING_GROUPS.get(key, 'general'),
                description=description
            )
            db.session.add(setting)
        else:
            setting.value = value
            if group:
                setting.group = group
            if description:
                setting.description = description
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        return False


def update_settings(updates_dict):
    """
    Bulk updates settings dictionary.
    """
    try:
        for k, v in updates_dict.items():
            setting = SystemSetting.query.filter_by(key=k).first()
            if not setting:
                setting = SystemSetting(
                    key=k,
                    value=v,
                    group=SETTING_GROUPS.get(k, 'general')
                )
                db.session.add(setting)
            else:
                setting.value = v
        db.session.commit()
        return True
    except Exception:
        db.session.rollback()
        return False


def init_default_settings():
    """
    Populates default settings in the database if they do not yet exist.
    """
    try:
        existing_keys = {s.key for s in SystemSetting.query.all()}
        added = False
        for k, v in DEFAULT_SETTINGS.items():
            if k not in existing_keys:
                db.session.add(SystemSetting(
                    key=k,
                    value=v,
                    group=SETTING_GROUPS.get(k, 'general')
                ))
                added = True
        if added:
            db.session.commit()
    except Exception:
        db.session.rollback()


def generate_secure_api_key():
    """Generates a secure random 32-byte hexadecimal API key for future ERP integrations."""
    return f"jp_live_{secrets.token_hex(24)}"
