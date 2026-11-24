"""
GROWTECH ENGINEERS — Storage Abstraction Module (storage.py)
Provides unified file storage supporting:
1. Supabase Storage (Production): Permanent cloud storage with zero Render disk reliance.
2. Local Filesystem (Development): Fallback to static/uploads when Supabase credentials are not set.

Ensures committed factory photography in static/images is protected and never modified/deleted.
"""

import os
import re
import uuid
import mimetypes
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime

# Whitelist of allowed extensions for industrial and media assets
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'svg', 'pdf', 'mp4', 'webm'}

# Factory static assets that must never be deleted
PROTECTED_PREFIXES = (
    'factory/',
    'customers/',
    'certificates/udyam_badge',
    'products/jigs_fixtures_real',
    'products/receiving_gauge_real',
    'products/press_tool_bending',
    'products/hydraulic_press_tool',
    'products/trolleys_racks_placeholder',
    'products/cooling_panel_real'
)

def get_upload_base():
    """Returns local base folder for uploads (development/fallback)"""
    upload_base = os.environ.get('UPLOAD_FOLDER')
    if not upload_base:
        upload_base = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
    return upload_base

def is_supabase_storage_enabled():
    """Checks whether Supabase Storage credentials are configured in the environment"""
    url = os.environ.get('SUPABASE_URL', '').strip()
    key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY') or os.environ.get('SUPABASE_KEY', '').strip()
    return bool(url and key)

def get_supabase_config():
    """Returns current Supabase configuration from environment"""
    url = os.environ.get('SUPABASE_URL', '').strip().rstrip('/')
    key = (os.environ.get('SUPABASE_SERVICE_ROLE_KEY') or os.environ.get('SUPABASE_KEY', '')).strip()
    bucket = os.environ.get('SUPABASE_BUCKET', 'growtech-uploads').strip()
    return url, key, bucket

def allowed_file(filename, custom_allowed=None):
    """Validates file extension against allowed whitelist"""
    if not filename or '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    allowed = custom_allowed if custom_allowed else ALLOWED_EXTENSIONS
    return ext in allowed

def generate_safe_filename(original_filename):
    """Generates a secure, collision-free filename using UUID and timestamp"""
    ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else 'jpg'
    return f"{uuid.uuid4().hex[:12]}_{int(datetime.now().timestamp())}.{ext}"

def get_supabase_public_url(object_path, bucket=None):
    """Constructs the permanent public URL for an object stored in Supabase Storage"""
    url, _, default_bucket = get_supabase_config()
    bucket_name = bucket or default_bucket
    clean_path = object_path.lstrip('/')
    return f"{url}/storage/v1/object/public/{bucket_name}/{clean_path}"

def upload_to_supabase(file_bytes, object_path, content_type=None, bucket=None):
    """
    Uploads raw file bytes to Supabase Storage via REST API.
    Returns the public URL on success or raises RuntimeError.
    """
    url, key, default_bucket = get_supabase_config()
    bucket_name = bucket or default_bucket
    clean_path = object_path.lstrip('/')

    if not content_type:
        content_type, _ = mimetypes.guess_type(clean_path)
    if not content_type:
        content_type = 'application/octet-stream'

    # Supabase Storage upload endpoint: POST /storage/v1/object/{bucket}/{path}
    endpoint = f"{url}/storage/v1/object/{bucket_name}/{clean_path}"

    headers = {
        'Authorization': f'Bearer {key}',
        'apiKey': key,
        'Content-Type': content_type,
        'x-upsert': 'true'
    }

    req = urllib.request.Request(endpoint, data=file_bytes, headers=headers, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            if response.status in (200, 201):
                return get_supabase_public_url(clean_path, bucket=bucket_name)
            else:
                raise RuntimeError(f"Supabase upload returned status {response.status}")
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8', errors='replace')
        raise RuntimeError(f"Supabase upload HTTP {e.code}: {error_body}")
    except Exception as e:
        raise RuntimeError(f"Supabase storage network error: {e}")

def delete_from_supabase(path_or_url, bucket=None):
    """
    Deletes an object from Supabase Storage given its public URL or storage path.
    Returns True on success or if already absent.
    """
    url, key, default_bucket = get_supabase_config()
    bucket_name = bucket or default_bucket
    object_path = path_or_url

    # Extract bucket and object path if full URL is passed
    if path_or_url.startswith('http://') or path_or_url.startswith('https://'):
        match = re.search(r'/storage/v1/object/(?:public/)?([^/]+)/(.+)$', path_or_url)
        if match:
            bucket_name = match.group(1)
            object_path = match.group(2)
        else:
            return False

    clean_path = object_path.lstrip('/')
    endpoint = f"{url}/storage/v1/object/{bucket_name}/{clean_path}"

    headers = {
        'Authorization': f'Bearer {key}',
        'apiKey': key
    }

    req = urllib.request.Request(endpoint, headers=headers, method='DELETE')
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            return response.status in (200, 204)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            # File already removed
            return True
        return False
    except Exception:
        return False

def is_protected_asset(path_or_url):
    """Checks whether the asset is a permanent factory photo that must never be deleted"""
    if not path_or_url:
        return True
    clean = path_or_url.replace('\\', '/').lstrip('/')
    for prefix in PROTECTED_PREFIXES:
        if clean.startswith(prefix):
            return True
    return False

def save_media(file_obj, subfolder, custom_allowed=None):
    """
    Central save method for all uploaded media:
    - If Supabase Storage is configured, uploads directly to Supabase and returns public URL.
    - Otherwise, saves to local static/uploads/ directory (for development).
    """
    if not file_obj or not getattr(file_obj, 'filename', None) or file_obj.filename == '':
        return None

    if not allowed_file(file_obj.filename, custom_allowed):
        return None

    safe_name = generate_safe_filename(file_obj.filename)
    subfolder_path = f"{subfolder}/{safe_name}"

    # Read binary content
    file_bytes = file_obj.read()
    if hasattr(file_obj, 'seek'):
        file_obj.seek(0)

    if is_supabase_storage_enabled():
        content_type = getattr(file_obj, 'content_type', None)
        return upload_to_supabase(file_bytes, subfolder_path, content_type=content_type)
    else:
        dest_folder = os.path.join(get_upload_base(), subfolder)
        os.makedirs(dest_folder, exist_ok=True)
        dest_path = os.path.join(dest_folder, safe_name)
        with open(dest_path, 'wb') as f:
            f.write(file_bytes)
        return f"uploads/{subfolder}/{safe_name}"

def delete_media(path_or_url):
    """
    Deletes an uploaded media item safely:
    - Never deletes committed factory photos in static/images.
    - If Supabase URL, deletes from Supabase Storage.
    - If local upload path, deletes from local UPLOAD_BASE.
    """
    if not path_or_url or is_protected_asset(path_or_url):
        return False

    if path_or_url.startswith('http://') or path_or_url.startswith('https://'):
        return delete_from_supabase(path_or_url)

    # Local upload path
    clean = path_or_url.replace('\\', '/').lstrip('/')
    if clean.startswith('uploads/'):
        clean = clean[len('uploads/'):]
    elif clean.startswith('static/uploads/'):
        clean = clean[len('static/uploads/'):]

    full_path = os.path.join(get_upload_base(), clean)
    if os.path.isfile(full_path):
        try:
            os.remove(full_path)
            return True
        except OSError:
            return False
    return False

def resolve_media_url(path):
    """
    Returns the complete, viewable URL for any media reference:
    - Empty: returns default logo
    - Full URL (Supabase Storage): returns as-is
    - Local upload ('uploads/...'): returns '/static/uploads/...'
    - Committed factory asset ('products/...'): returns '/static/images/products/...'
    """
    if not path:
        return '/static/images/logo.png'

    path_str = str(path).strip()
    if path_str.startswith('http://') or path_str.startswith('https://'):
        return path_str

    clean = path_str.replace('\\', '/').lstrip('/')
    if clean.startswith('uploads/'):
        return f"/static/{clean}"
    if clean.startswith('static/'):
        return f"/{clean}"

    return f"/static/images/{clean}"
