import re
import secrets
from extensions import db
from models.system_setting import SystemSetting

THEME_PRESETS = {
    'indigo': {
        'id': 'indigo',
        'name': 'Indigo / Royal Blue',
        'primary': '#2563EB',
        'dot': 'bg-blue-600',
        'preview_class': 'border-blue-600',
    },
    'emerald': {
        'id': 'emerald',
        'name': 'Emerald Green',
        'primary': '#059669',
        'dot': 'bg-emerald-600',
        'preview_class': 'border-emerald-600',
    },
    'rose': {
        'id': 'rose',
        'name': 'Rose Crimson',
        'primary': '#E11D48',
        'dot': 'bg-rose-600',
        'preview_class': 'border-rose-600',
    },
    'amber': {
        'id': 'amber',
        'name': 'Amber Gold',
        'primary': '#D97706',
        'dot': 'bg-amber-600',
        'preview_class': 'border-amber-600',
    },
    'purple': {
        'id': 'purple',
        'name': 'Violet Purple',
        'primary': '#7C3AED',
        'dot': 'bg-purple-600',
        'preview_class': 'border-purple-600',
    },
    'cyan': {
        'id': 'cyan',
        'name': 'Ocean Cyan',
        'primary': '#0284C7',
        'dot': 'bg-cyan-600',
        'preview_class': 'border-cyan-600',
    },
    'slate': {
        'id': 'slate',
        'name': 'Slate Gray',
        'primary': '#334155',
        'dot': 'bg-slate-700',
        'preview_class': 'border-slate-700',
    },
    'dark': {
        'id': 'dark',
        'name': 'Midnight Dark',
        'primary': '#0F172A',
        'dot': 'bg-neutral-900',
        'preview_class': 'border-gray-900',
    },
}

DEFAULT_SETTINGS = {
    # Admin Portal Identity (shows different from the main website)
    'admin_portal_name': 'JobPortal Admin Suite',
    'admin_portal_tagline': 'Executive ERP & Operations Console',
    'admin_portal_logo': '',
    'admin_theme': 'indigo',  # 'slate', 'dark', 'indigo', 'rose', 'emerald', etc., or hex code
    'theme_color': '',  # Canonical hex color code for dynamic theme & website primary
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
    'theme_color': 'admin_portal',
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


def normalize_hex_color(hex_str, default='#2563EB'):
    """Validates and normalizes hex color code (#RGB or #RRGGBB)."""
    if not hex_str or not isinstance(hex_str, str):
        return default
    hex_str = hex_str.strip()
    if not hex_str.startswith('#'):
        hex_str = '#' + hex_str
    
    if re.match(r'^#[0-9a-fA-F]{6}$', hex_str):
        return hex_str.upper()
    elif re.match(r'^#[0-9a-fA-F]{3}$', hex_str):
        return ('#' + ''.join([c * 2 for c in hex_str[1:]])).upper()
    return default


def hex_to_rgb(hex_str):
    """Converts hex code to RGB tuple."""
    hex_str = normalize_hex_color(hex_str).lstrip('#')
    return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb):
    """Converts RGB tuple/list to 6-char hex string."""
    r = int(max(0, min(255, round(rgb[0]))))
    g = int(max(0, min(255, round(rgb[1]))))
    b = int(max(0, min(255, round(rgb[2]))))
    return f"#{r:02X}{g:02X}{b:02X}"


def mix_color(c1, c2, weight):
    """Blends two RGB colors: weight is proportion of c1 (0.0 to 1.0)."""
    return (
        c1[0] * weight + c2[0] * (1.0 - weight),
        c1[1] * weight + c2[1] * (1.0 - weight),
        c1[2] * weight + c2[2] * (1.0 - weight),
    )


def generate_theme_palette(base_hex):
    """
    Generates a full 10-shade design token palette (50-900) + RGB and contrast text
    from any base hex color.
    """
    base_hex = normalize_hex_color(base_hex)
    c = hex_to_rgb(base_hex)
    white = (255, 255, 255)
    black = (0, 0, 0)

    # Relative luminance calculation for accessibility
    lum = (0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]) / 255.0
    contrast_text = '#0f172a' if lum > 0.65 else '#ffffff'

    # Check if matches any preset key
    matched_preset = None
    for k, v in THEME_PRESETS.items():
        if v['primary'].upper() == base_hex.upper():
            matched_preset = k
            break

    return {
        '50': rgb_to_hex(mix_color(c, white, 0.08)),
        '100': rgb_to_hex(mix_color(c, white, 0.18)),
        '200': rgb_to_hex(mix_color(c, white, 0.32)),
        '300': rgb_to_hex(mix_color(c, white, 0.50)),
        '400': rgb_to_hex(mix_color(c, white, 0.75)),
        '500': rgb_to_hex(mix_color(c, white, 0.90)),
        '600': base_hex,
        '700': rgb_to_hex(mix_color(c, black, 0.85)),
        '800': rgb_to_hex(mix_color(c, black, 0.70)),
        '900': rgb_to_hex(mix_color(c, black, 0.50)),
        'rgb': f"{c[0]}, {c[1]}, {c[2]}",
        'contrast': contrast_text,
        'primary': base_hex,
        'primary_hover': rgb_to_hex(mix_color(c, black, 0.85)),
        'primary_light': rgb_to_hex(mix_color(c, white, 0.08)),
        'primary_dark': rgb_to_hex(mix_color(c, black, 0.70)),
        'preset_key': matched_preset or 'custom',
        'preset_name': THEME_PRESETS[matched_preset]['name'] if matched_preset else 'Custom Accent',
        'is_preset': matched_preset is not None,
    }


def resolve_theme_color(theme_val, default='#2563EB'):
    """
    Resolves either a preset name (e.g., 'emerald', 'rose') or hex code into a valid hex color.
    """
    if not theme_val:
        return default
    val = str(theme_val).strip().lower()
    if val in THEME_PRESETS:
        return THEME_PRESETS[val]['primary']
    return normalize_hex_color(theme_val, default=default)


import os


def is_valid_branding_file(filename):
    """Verifies that a branding image file exists on disk and is not an empty file."""
    if not filename or not isinstance(filename, str):
        return False
    from config import Config
    path = os.path.join(Config.BRANDING_FOLDER, filename)
    return os.path.exists(path) and os.path.getsize(path) > 0


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

        # Smart Theme Resolution
        admin_theme = settings.get('admin_theme', 'indigo')
        theme_color = settings.get('theme_color', '')
        if not theme_color:
            theme_color = resolve_theme_color(admin_theme)
            settings['theme_color'] = theme_color
        else:
            theme_color = normalize_hex_color(theme_color)
            settings['theme_color'] = theme_color

        palette = generate_theme_palette(theme_color)
        settings['theme_palette'] = palette
        settings['theme_presets'] = THEME_PRESETS

    except Exception:
        # If database table is not yet initialized or during migrations, return defaults
        settings['theme_color'] = '#2563EB'
        settings['theme_palette'] = generate_theme_palette('#2563EB')
        settings['theme_presets'] = THEME_PRESETS
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
