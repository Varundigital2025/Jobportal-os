import os
import uuid
from werkzeug.utils import secure_filename
from flask import current_app


def allowed_file(filename, allowed_extensions):
    if not filename or '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in allowed_extensions


def save_upload_file(file_storage, folder, allowed_extensions, prefix=''):
    """
    Saves an uploaded file safely:
    - Verifies extension against raw filename (handles unicode / international filenames)
    - Generates a UUID filename to prevent collision and directory traversal
    - Retains original clean file extension
    Returns: (saved_filename, error_message)
    """
    if not file_storage or not file_storage.filename or not file_storage.filename.strip():
        return None, "No file provided"

    raw_filename = file_storage.filename.strip()
    if not allowed_file(raw_filename, allowed_extensions):
        ext_list = ", ".join(sorted(allowed_extensions))
        return None, f"Invalid file format. Allowed formats: {ext_list}"

    ext = raw_filename.rsplit('.', 1)[1].lower()
    unique_token = uuid.uuid4().hex[:12]
    safe_filename = f"{prefix}{unique_token}.{ext}" if prefix else f"{unique_token}.{ext}"
    
    os.makedirs(folder, exist_ok=True)
    full_path = os.path.join(folder, safe_filename)
    try:
        if hasattr(file_storage, 'seek'):
            file_storage.seek(0)
        file_storage.save(full_path)
    except Exception as e:
        return None, f"Failed to save file to disk: {str(e)}"

    return safe_filename, None


def save_resume(file_storage):
    """Saves candidate resume."""
    from config import Config
    return save_upload_file(
        file_storage,
        Config.RESUME_FOLDER,
        Config.ALLOWED_RESUME_EXTENSIONS,
        prefix='resume_'
    )


def save_profile_photo(file_storage):
    """Saves user profile photo."""
    from config import Config
    return save_upload_file(
        file_storage,
        Config.PHOTO_FOLDER,
        Config.ALLOWED_IMAGE_EXTENSIONS,
        prefix='photo_'
    )


def save_company_logo(file_storage):
    """Saves employer company logo."""
    from config import Config
    return save_upload_file(
        file_storage,
        Config.LOGO_FOLDER,
        Config.ALLOWED_IMAGE_EXTENSIONS,
        prefix='logo_'
    )


def save_branding_image(file_storage, prefix='brand_'):
    """Saves admin portal logo or main website branding image."""
    from config import Config
    return save_upload_file(
        file_storage,
        Config.BRANDING_FOLDER,
        Config.ALLOWED_BRANDING_EXTENSIONS,
        prefix=prefix
    )

