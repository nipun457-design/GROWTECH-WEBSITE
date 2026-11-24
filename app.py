import os
import re
import json
import uuid
import secrets
import sqlite3
from datetime import datetime, timedelta
from functools import wraps
from flask import (
    Flask, render_template, request, flash, redirect,
    url_for, session, g, abort, send_from_directory, jsonify
)
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
import db
import storage

app = Flask(__name__)

# Register media_url directly on Jinja environment (filter and global function)
app.jinja_env.filters['media_url'] = storage.resolve_media_url
app.jinja_env.globals['media_url'] = storage.resolve_media_url
app.jinja_env.auto_reload = True

# --- Production Environment Configuration ---
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'growtech-engineers-industrial-sec-2023')
app.config['DEBUG'] = os.environ.get('FLASK_DEBUG', 'false').lower() in ('true', '1', 't')
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max upload
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=4)
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
# Secure cookies enabled when HTTPS is active or configured in environment
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('SESSION_COOKIE_SECURE', 'false').lower() in ('true', '1', 't')

DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'growtech.db')

# Persistent Disk Storage path or local static/uploads fallback
UPLOAD_BASE = os.environ.get('UPLOAD_FOLDER')
if not UPLOAD_BASE:
    UPLOAD_BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'svg', 'pdf', 'mp4', 'webm'}

# Ensure upload folders exist
for folder in ['products', 'gallery', 'certificates', 'news']:
    os.makedirs(os.path.join(UPLOAD_BASE, folder), exist_ok=True)

# --- Database Setup & Helper Functions ---
def get_db():
    db_conn = getattr(g, '_database', None)
    if db_conn is None:
        db_conn = g._database = db.get_connection()
    return db_conn

@app.teardown_appcontext
def close_connection(exception):
    db_conn = getattr(g, '_database', None)
    if db_conn is not None:
        db_conn.close()

def init_db():
    from migrate_phase2 import migrate
    with app.app_context():
        migrate()

# Initialize DB tables & seed if empty
init_db()

# --- Persistent File Serving with Path Traversal Protection ---
@app.route('/static/uploads/<path:filename>')
@app.route('/uploads/<path:filename>')
def serve_uploaded_file(filename):
    """Safely serves uploaded media from persistent storage with strict path traversal checks"""
    safe_path = os.path.normpath(filename).lstrip(r'\/')
    if '..' in safe_path.split(os.path.sep):
        abort(403)
    
    # 1. Check persistent/local storage directory
    full_path = os.path.join(UPLOAD_BASE, safe_path)
    if os.path.isfile(full_path):
        folder_dir = os.path.dirname(full_path)
        base_file = os.path.basename(full_path)
        return send_from_directory(folder_dir, base_file)
    
    # 2. Check local static/uploads directory as fallback
    local_uploads = os.path.join(app.root_path, 'static', 'uploads')
    local_full = os.path.join(local_uploads, safe_path)
    if os.path.isfile(local_full):
        folder_dir = os.path.dirname(local_full)
        base_file = os.path.basename(local_full)
        return send_from_directory(folder_dir, base_file)
    
    # 3. If Supabase Storage is enabled, redirect to cloud asset
    if storage.is_supabase_storage_enabled():
        return redirect(storage.get_supabase_public_url(safe_path))
        
    abort(404)

# --- Health Check Endpoint (Render & Uptime Monitoring) ---
@app.route('/api/health')
def health_check():
    """Health check endpoint for Render, load balancers, and external monitoring"""
    db_status = "connected"
    try:
        conn = get_db()
        conn.execute("SELECT 1")
    except Exception:
        db_status = "unavailable"
    
    status_code = 200 if db_status == "connected" else 503
    return jsonify({
        "status": "healthy" if db_status == "connected" else "degraded",
        "service": "GROWTECH ENGINEERS Corporate Web Application",
        "database": db_status,
        "environment": "production" if not app.debug else "development",
        "timestamp": datetime.now().isoformat()
    }), status_code

# --- Security & CSRF Protection ---
def generate_csrf_token():
    if '_csrf_token' not in session:
        session['_csrf_token'] = secrets.token_hex(32)
    return session['_csrf_token']

def verify_csrf_token():
    token = request.form.get('csrf_token') or request.headers.get('X-CSRFToken')
    if not token or token != session.get('_csrf_token'):
        abort(403)

def allowed_file(filename, custom_allowed=None):
    return storage.allowed_file(filename, custom_allowed=custom_allowed)

def save_uploaded_file(file_obj, subfolder, custom_allowed=None):
    return storage.save_media(file_obj, subfolder, custom_allowed=custom_allowed)

def delete_uploaded_file(path_or_url):
    return storage.delete_media(path_or_url)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_user_id' not in session:
            flash('Please log in with an authorized owner account to access the dashboard.', 'warning')
            return redirect(url_for('admin_login', next=request.path))
        return f(*args, **kwargs)
    return decorated_function

# --- Cache-Control for HTML Pages ---
@app.after_request
def add_no_cache_headers(response):
    """Ensure HTML pages are not cached by browsers during development or updates"""
    if response.content_type and 'text/html' in response.content_type:
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    return response

# --- CSRF & Global Context Processors ---
@app.context_processor
def inject_csrf():
    return dict(csrf_token=generate_csrf_token)

# --- Media URL Helper & Jinja Filter ---
@app.template_filter('media_url')
def media_url_filter(path):
    return storage.resolve_media_url(path)

@app.context_processor
def inject_media_url():
    return dict(media_url=storage.resolve_media_url)

# --- Customer Logos from Genuine Company Profile ---
GENUINE_CUSTOMERS = [
    {'name': 'Toyota Boshoku', 'image': 'customers/toyota_boshoku.png', 'sector': 'Automotive Interior Systems'},
    {'name': 'Nitto', 'image': 'customers/nitto.jpg', 'sector': 'Industrial Materials & Tapes'},
    {'name': 'AtMa (Atma Autotech)', 'image': 'customers/atma.jpg', 'sector': 'Automotive Component Manufacturing'},
    {'name': 'Onassis Auto', 'image': 'customers/onassis_auto.jpg', 'sector': 'Automotive Precision Engineering'},
    {'name': 'NSSI', 'image': 'customers/nssi.png', 'sector': 'Industrial Systems'},
    {'name': 'SE', 'image': 'customers/se.jpg', 'sector': 'Precision Engineering'},
    {'name': 'SFC (part of amaneos)', 'image': 'customers/sfc_amaneos.jpg', 'sector': 'Fluid Handling & Sealing Solutions'},
    {'name': 'Wahi Sons', 'image': 'customers/wahi_sons.jpg', 'sector': 'Automotive Fasteners & Precision Parts'},
    {'name': 'Hi-Lex Act', 'image': 'customers/hilex_act.jpg', 'sector': 'Control Cables & Actuation Systems'}
]

@app.context_processor
def inject_company_info():
    """Dynamically loads company content from DB with robust fallbacks"""
    db = get_db()
    content_map = {}
    try:
        cursor = db.execute("SELECT key_name, value FROM company_content")
        for row in cursor.fetchall():
            content_map[row['key_name']] = row['value']
    except Exception:
        pass

    phone_primary = content_map.get('phone_primary', '+91-9991535590')
    phone_secondary = content_map.get('phone_secondary', '+91-9991535590')
    phone_p_clean = re.sub(r'[\s\-\(\)\+]', '', phone_primary)
    phone_s_clean = re.sub(r'[\s\-\(\)\+]', '', phone_secondary)

    company_info = {
        'name': content_map.get('company_name', 'GROWTECH ENGINEERS'),
        'legal_name': content_map.get('company_name', 'Growtech Engineers'),
        'short_name': 'GROWTECH',
        'tagline': content_map.get('tagline', 'Precision Tooling, Jigs & Fixtures, and Industrial Engineering Solutions'),
        'slogan': content_map.get('slogan', "GTE – Let's Get Growing"),
        'business': content_map.get('business', 'Manufacturing machine components, parts, tooling, and industrial engineering solutions'),
        'proprietor': content_map.get('proprietor', 'Mr. Naresh Kumar'),
        'proprietor_experience': content_map.get('proprietor_experience', '22+ Years of Engineering & Toolroom Experience'),
        'established': content_map.get('established', 'September 2023'),
        'gstin': content_map.get('gstin', '06BIYPK7127F1ZV'),
        'udyam_number': content_map.get('udyam_number', 'UDYAM-HR-05-0093212'),
        'udyam_type': content_map.get('udyam_type', 'Micro Enterprise (Manufacturing)'),
        'nic_code': content_map.get('nic_code', '28221 (Metal-forming machinery & machine tools)'),
        'email': content_map.get('email', 'growtechengineers911@gmail.com'),
        'phone_primary': phone_primary,
        'phone_secondary': phone_secondary,
        'phone_primary_raw': f"+{phone_p_clean}" if not phone_primary.startswith('+') else phone_primary,
        'phone_secondary_raw': f"+{phone_s_clean}" if not phone_secondary.startswith('+') else phone_secondary,
        'whatsapp_url_1': f"https://wa.me/{phone_p_clean}?text=Hello%20Growtech%20Engineers,%20I%20have%20an%20enquiry%20regarding%20tooling%20and%20manufacturing%20services.",
        'whatsapp_url_2': f"https://wa.me/{phone_s_clean}?text=Hello%20Growtech%20Engineers,%20I%20have%20an%20enquiry%20regarding%20tooling%20and%20manufacturing%20services.",
        'location': content_map.get('location', 'Main Market, Fazalwas, Tauru Road, Pachgaon, Manesar, Gurugram, Haryana – 122413, India'),
        'city': content_map.get('city', 'Manesar, Gurugram'),
        'state': content_map.get('state', 'Haryana'),
        'pincode': content_map.get('pincode', '122413'),
        'instagram': '@growtechengineers_911',
        'instagram_url': 'https://instagram.com/growtechengineers_911',
        'working_hours': content_map.get('working_hours', 'Monday – Saturday: 08:30 AM – 07:30 PM (Sunday Closed)'),
        'facilities_area': content_map.get('facilities_area', 'Total Area: 3,800 Sq. Ft. | Built-up Area: 2,650 Sq. Ft.'),
        'manpower': content_map.get('manpower', '8 Technical Team Members (Fabrication, Automation & Tool/Fixture Mfg.)'),
        'power_backup': content_map.get('power_backup', '35 KVA Generator Facility Available'),
        'vision': content_map.get('vision', "TO PROVIDE THE ENGINEERING SOLUTIONS TO MAKE EVERYONE'S LIFE EASY & TO WIN THE CONFIDENCE OF STAKEHOLDERS."),
        'mission': content_map.get('mission', "TO MAKE OUR ORGANIZATION BEST IN THE MARKET TO PROVIDE INDUSTRIAL SOLUTIONS WITH EFFECTIVE COST."),
        'intro_text': content_map.get('intro_text', "Established in September 2023 by Mr. Naresh Kumar (bringing over 22 years of hands-on tooling experience), GROWTECH ENGINEERS (GTE) has positioned itself as a dependable tooling, machining, and engineering partner for component manufacturers in the Gurgaon–Manesar industrial belt."),
        'core_services': [
            'Jigs and Fixtures',
            'Receiving Gauges',
            'Tandem Press Tools & Dies',
            'Hydraulic Presses',
            'Trolleys and Racks',
            'Engineering Solutions'
        ],
        'customers': GENUINE_CUSTOMERS,
        'current_year': datetime.now().year
    }

    # Count unread enquiries for badge in admin
    unread_count = 0
    try:
        c = db.execute("SELECT COUNT(*) as cnt FROM enquiries WHERE status = 'New'")
        unread_count = c.fetchone()['cnt']
    except Exception:
        pass

    return dict(company=company_info, unread_enquiries_count=unread_count)

# --- Helper to deserialize features & applications ---
def process_product_row(row):
    p = dict(row)
    try:
        p['features'] = json.loads(p.get('features') or '[]')
    except Exception:
        p['features'] = [f.strip() for f in (p.get('features') or '').split('\n') if f.strip()]
    try:
        p['applications'] = json.loads(p.get('applications') or '[]')
    except Exception:
        p['applications'] = [a.strip() for a in (p.get('applications') or '').split('\n') if a.strip()]
    return p

# =========================================================================
# PUBLIC WEBSITE ROUTES (Dynamic Integration with Database)
# =========================================================================

@app.route('/')
def home():
    """Homepage route - dynamically loads published products and news from DB"""
    db = get_db()
    cursor = db.execute('''
        SELECT * FROM products WHERE is_published = 1 ORDER BY is_featured DESC, id ASC LIMIT 4
    ''')
    featured_products = [process_product_row(row) for row in cursor.fetchall()]

    all_cursor = db.execute('''
        SELECT * FROM products WHERE is_published = 1 ORDER BY id ASC
    ''')
    all_products = [process_product_row(row) for row in all_cursor.fetchall()]

    return render_template(
        'index.html',
        active_page='home',
        featured_products=featured_products,
        all_products=all_products,
        media_url=storage.resolve_media_url
    )

@app.route('/company')
def company():
    """Company profile, vision, mission, infrastructure, and team"""
    return render_template('company.html', active_page='company')

@app.route('/products')
def products():
    """Products and manufacturing capabilities catalog - dynamic from DB"""
    category_filter = request.args.get('category', '').strip().lower()
    db = get_db()
    cursor = db.execute('''
        SELECT * FROM products WHERE is_published = 1 ORDER BY id ASC
    ''')
    products_list = [process_product_row(row) for row in cursor.fetchall()]

    return render_template(
        'products.html',
        active_page='products',
        products=products_list,
        selected_category=category_filter
    )

@app.route('/news')
def news():
    """News, company events, and confirmed manufacturing milestones - dynamic from DB"""
    db = get_db()
    cursor = db.execute('''
        SELECT * FROM news_items WHERE is_published = 1 ORDER BY id DESC
    ''')
    news_items = [dict(row) for row in cursor.fetchall()]
    return render_template('news.html', active_page='news', news_items=news_items)

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    """Contact page with company coordinates and enquiry form"""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        company_name = request.form.get('company_name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        subject = request.form.get('subject', '').strip()
        service_category = request.form.get('service_category', '').strip()
        message = request.form.get('message', '').strip()

        if not subject and service_category:
            subject = f"Enquiry regarding {service_category}"

        # Validation
        errors = []
        if not name or len(name) < 2:
            errors.append('Please provide your full name (minimum 2 characters).')
        
        email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        if not email or not re.match(email_pattern, email):
            errors.append('Please provide a valid business email address.')

        phone_clean = re.sub(r'[\s\-\(\)\+]', '', phone)
        if not phone or len(phone_clean) < 8 or not phone_clean.isdigit():
            errors.append('Please provide a valid contact phone number (at least 8 digits).')

        if not subject or len(subject) < 3:
            errors.append('Please provide an enquiry subject (minimum 3 characters).')

        if not message or len(message) < 10:
            errors.append('Please write a brief description of your requirement (minimum 10 characters).')

        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('contact.html', active_page='contact', form_data=request.form)

        # Insert into SQLite DB
        try:
            ip_address = request.remote_addr or '127.0.0.1'
            db = get_db()
            db.execute('''
                INSERT INTO enquiries (name, company_name, email, phone, subject, service_category, message, ip_address)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (name, company_name, email, phone, subject, service_category, message, ip_address))
            db.commit()

            flash('Thank you for contacting GROWTECH ENGINEERS. Your enquiry has been received successfully. Our engineering team will review your specifications and contact you shortly.', 'success')
            return redirect(url_for('contact'))
        except Exception as e:
            app.logger.error(f"Error saving enquiry: {e}")
            flash('An unexpected error occurred while submitting your enquiry. Please call us directly or message us on WhatsApp.', 'warning')
            return render_template('contact.html', active_page='contact', form_data=request.form)

    return render_template('contact.html', active_page='contact', form_data={})

# =========================================================================
# PRIVATE OWNER ADMIN DASHBOARD ROUTES
# =========================================================================

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Private Owner Admin Login"""
    if 'admin_user_id' in session:
        return redirect(url_for('admin_dashboard'))

    next_url = request.args.get('next') or request.form.get('next')

    if request.method == 'POST':
        verify_csrf_token()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if not username or not password:
            flash('Please enter both username and password.', 'danger')
            return render_template('admin/login.html', next_url=next_url)

        db = get_db()
        cursor = db.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()

        if user and check_password_hash(user['password_hash'], password):
            # Session setup
            session.permanent = True
            session['admin_user_id'] = user['id']
            session['admin_username'] = user['username']
            session['admin_user_name'] = user['full_name'] or user['username']
            session['admin_role'] = user['role']

            # Update last login timestamp
            db.execute("UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?", (user['id'],))
            db.commit()

            flash(f"Welcome back, {session['admin_user_name']}!", 'success')
            if next_url and next_url.startswith('/admin'):
                return redirect(next_url)
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid administrator credentials. Access is restricted to authorized owners.', 'danger')
            return render_template('admin/login.html', next_url=next_url)

    return render_template('admin/login.html', next_url=next_url)

@app.route('/admin/logout')
def admin_logout():
    """Logout admin session"""
    session.clear()
    flash('You have been logged out securely.', 'info')
    return redirect(url_for('admin_login'))

@app.route('/admin')
@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    """Main owner admin dashboard overview"""
    db = get_db()

    # Calculate statistics
    total_products = db.execute("SELECT COUNT(*) as c FROM products").fetchone()['c']
    published_products = db.execute("SELECT COUNT(*) as c FROM products WHERE is_published = 1").fetchone()['c']
    total_enquiries = db.execute("SELECT COUNT(*) as c FROM enquiries").fetchone()['c']
    new_enquiries = db.execute("SELECT COUNT(*) as c FROM enquiries WHERE status = 'New'").fetchone()['c']
    total_gallery = db.execute("SELECT COUNT(*) as c FROM gallery").fetchone()['c']
    total_news = db.execute("SELECT COUNT(*) as c FROM news_items").fetchone()['c']

    # Fetch recent enquiries
    recent_enquiries = db.execute('''
        SELECT * FROM enquiries ORDER BY id DESC LIMIT 5
    ''').fetchall()

    # Fetch recent products
    recent_products = db.execute('''
        SELECT * FROM products ORDER BY id DESC LIMIT 5
    ''').fetchall()

    stats = {
        'total_products': total_products,
        'published_products': published_products,
        'total_enquiries': total_enquiries,
        'new_enquiries': new_enquiries,
        'total_gallery': total_gallery,
        'total_news': total_news
    }

    return render_template(
        'admin/dashboard.html',
        active_admin='dashboard',
        stats=stats,
        recent_enquiries=recent_enquiries,
        recent_products=recent_products
    )

# --- Product Management Routes ---

@app.route('/admin/products')
@login_required
def admin_products():
    """List all products in admin"""
    db = get_db()
    products_list = db.execute("SELECT * FROM products ORDER BY id DESC").fetchall()
    return render_template('admin/products_list.html', active_admin='products', products=products_list)

@app.route('/admin/products/add', methods=['GET', 'POST'])
@login_required
def admin_product_add():
    """Add a new product"""
    if request.method == 'POST':
        verify_csrf_token()
        title = request.form.get('title', '').strip()
        category = request.form.get('category', '').strip()
        tag = request.form.get('tag', '').strip()
        summary = request.form.get('summary', '').strip()
        description = request.form.get('description', '').strip()
        features_raw = request.form.get('features', '').strip()
        apps_raw = request.form.get('applications', '').strip()
        video_url = request.form.get('video_url', '').strip()
        status_note = request.form.get('status_note', '').strip()
        is_featured = 1 if request.form.get('is_featured') else 0
        is_published = 1 if request.form.get('is_published') else 0

        # Generate slug
        slug = re.sub(r'[^a-zA-Z0-9]+', '-', title).strip('-').lower()
        if not slug:
            slug = f"product-{uuid.uuid4().hex[:6]}"

        category_slug = re.sub(r'[^a-zA-Z0-9]+', '-', category).strip('-').lower()

        # Handle features & applications
        features_list = [f.strip() for f in features_raw.split('\n') if f.strip()]
        apps_list = [a.strip() for a in apps_raw.split('\n') if a.strip()]

        # Handle primary image
        primary_file = request.files.get('primary_image')
        image_path = save_uploaded_file(primary_file, 'products')
        if not image_path:
            flash('Please upload a valid primary product image (JPG, PNG, WEBP).', 'danger')
            return render_template('admin/product_form.html', active_admin='products', product=None)

        db = get_db()
        cursor = db.execute('''
            INSERT INTO products (title, slug, category, category_slug, tag, summary, description, features, applications, image, video_url, is_featured, is_published, status_note)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (title, slug, category, category_slug, tag, summary, description, json.dumps(features_list), json.dumps(apps_list), image_path, video_url, is_featured, is_published, status_note))
        product_id = cursor.lastrowid

        # Insert into product_images
        db.execute('''
            INSERT INTO product_images (product_id, image_path, caption, is_primary)
            VALUES (?, ?, ?, 1)
        ''', (product_id, image_path, title))

        # Handle additional multiple photos
        add_files = request.files.getlist('additional_images')
        for f in add_files:
            extra_path = save_uploaded_file(f, 'products')
            if extra_path:
                db.execute('''
                    INSERT INTO product_images (product_id, image_path, caption, is_primary)
                    VALUES (?, ?, ?, 0)
                ''', (product_id, extra_path, title))

        db.commit()
        flash(f"Product '{title}' added successfully!", 'success')
        return redirect(url_for('admin_products'))

    return render_template('admin/product_form.html', active_admin='products', product=None)

@app.route('/admin/products/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def admin_product_edit(id):
    """Edit an existing product"""
    db = get_db()
    product = db.execute("SELECT * FROM products WHERE id = ?", (id,)).fetchone()
    if not product:
        flash('Product not found.', 'danger')
        return redirect(url_for('admin_products'))

    if request.method == 'POST':
        verify_csrf_token()
        title = request.form.get('title', '').strip()
        category = request.form.get('category', '').strip()
        tag = request.form.get('tag', '').strip()
        summary = request.form.get('summary', '').strip()
        description = request.form.get('description', '').strip()
        features_raw = request.form.get('features', '').strip()
        apps_raw = request.form.get('applications', '').strip()
        video_url = request.form.get('video_url', '').strip()
        status_note = request.form.get('status_note', '').strip()
        is_featured = 1 if request.form.get('is_featured') else 0
        is_published = 1 if request.form.get('is_published') else 0

        category_slug = re.sub(r'[^a-zA-Z0-9]+', '-', category).strip('-').lower()
        features_list = [f.strip() for f in features_raw.split('\n') if f.strip()]
        apps_list = [a.strip() for a in apps_raw.split('\n') if a.strip()]

        # Handle optional replacement of primary image
        image_path = product['image']
        primary_file = request.files.get('primary_image')
        new_image = save_uploaded_file(primary_file, 'products')
        if new_image:
            if image_path and image_path != new_image:
                delete_uploaded_file(image_path)
            image_path = new_image
            # Update primary in product_images
            db.execute("UPDATE product_images SET is_primary = 0 WHERE product_id = ?", (id,))
            db.execute("INSERT INTO product_images (product_id, image_path, caption, is_primary) VALUES (?, ?, ?, 1)", (id, new_image, title))

        db.execute('''
            UPDATE products
            SET title = ?, category = ?, category_slug = ?, tag = ?, summary = ?, description = ?,
                features = ?, applications = ?, image = ?, video_url = ?, is_featured = ?, is_published = ?,
                status_note = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (title, category, category_slug, tag, summary, description, json.dumps(features_list), json.dumps(apps_list), image_path, video_url, is_featured, is_published, status_note, id))

        # Handle additional photos upload
        add_files = request.files.getlist('additional_images')
        for f in add_files:
            extra_path = save_uploaded_file(f, 'products')
            if extra_path:
                db.execute('''
                    INSERT INTO product_images (product_id, image_path, caption, is_primary)
                    VALUES (?, ?, ?, 0)
                ''', (id, extra_path, title))

        db.commit()
        flash(f"Product '{title}' updated successfully!", 'success')
        return redirect(url_for('admin_products'))

    # Load features and applications as multiline string for form
    features_data = []
    try:
        features_data = json.loads(product['features'] or '[]')
    except Exception:
        features_data = [f.strip() for f in (product['features'] or '').split('\n') if f.strip()]

    apps_data = []
    try:
        apps_data = json.loads(product['applications'] or '[]')
    except Exception:
        apps_data = [a.strip() for a in (product['applications'] or '').split('\n') if a.strip()]

    additional_images = db.execute("SELECT * FROM product_images WHERE product_id = ? AND is_primary = 0", (id,)).fetchall()

    return render_template(
        'admin/product_form.html',
        active_admin='products',
        product=product,
        features_text='\n'.join(features_data),
        applications_text='\n'.join(apps_data),
        additional_images=additional_images
    )

@app.route('/admin/products/toggle/<int:id>', methods=['POST'])
@login_required
def admin_product_toggle(id):
    """Toggle publish/unpublish product"""
    verify_csrf_token()
    db = get_db()
    product = db.execute("SELECT is_published, title FROM products WHERE id = ?", (id,)).fetchone()
    if product:
        new_status = 0 if product['is_published'] else 1
        db.execute("UPDATE products SET is_published = ? WHERE id = ?", (new_status, id))
        db.commit()
        state_str = "published" if new_status else "unpublished"
        flash(f"Product '{product['title']}' is now {state_str}.", 'info')
    return redirect(url_for('admin_products'))

@app.route('/admin/products/delete/<int:id>', methods=['POST'])
@login_required
def admin_product_delete(id):
    """Delete a product"""
    verify_csrf_token()
    db = get_db()
    product = db.execute("SELECT title, image FROM products WHERE id = ?", (id,)).fetchone()
    if product:
        if product['image']:
            delete_uploaded_file(product['image'])
        photos = db.execute("SELECT image_path FROM product_images WHERE product_id = ?", (id,)).fetchall()
        for p in photos:
            delete_uploaded_file(p['image_path'])
        db.execute("DELETE FROM product_images WHERE product_id = ?", (id,))
        db.execute("DELETE FROM products WHERE id = ?", (id,))
        db.commit()
        flash(f"Product '{product['title']}' was deleted.", 'success')
    return redirect(url_for('admin_products'))

# --- Company Content Management ---

@app.route('/admin/company', methods=['GET', 'POST'])
@login_required
def admin_company():
    """Manage company content, coordinates, and details"""
    db = get_db()
    if request.method == 'POST':
        verify_csrf_token()
        fields = [
            'company_name', 'slogan', 'tagline', 'business', 'proprietor',
            'proprietor_experience', 'established', 'gstin', 'udyam_number',
            'udyam_type', 'nic_code', 'phone_primary', 'phone_secondary',
            'email', 'location', 'facilities_area', 'manpower', 'power_backup',
            'working_hours', 'vision', 'mission', 'intro_text'
        ]
        for field in fields:
            val = request.form.get(field, '').strip()
            db.execute('''
                INSERT INTO company_content (key_name, value, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(key_name) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP
            ''', (field, val))
        db.commit()
        flash('Company profile and settings updated successfully! Changes are live on the public site.', 'success')
        return redirect(url_for('admin_company'))

    cursor = db.execute("SELECT key_name, value FROM company_content")
    content = {row['key_name']: row['value'] for row in cursor.fetchall()}
    return render_template('admin/company_form.html', active_admin='company', content=content)

# --- Gallery Management Routes ---

@app.route('/admin/gallery')
@login_required
def admin_gallery():
    """List gallery items"""
    db = get_db()
    items = db.execute("SELECT * FROM gallery ORDER BY id DESC").fetchall()
    return render_template('admin/gallery_list.html', active_admin='gallery', items=items)

@app.route('/admin/gallery/add', methods=['GET', 'POST'])
@login_required
def admin_gallery_add():
    """Upload new gallery media"""
    if request.method == 'POST':
        verify_csrf_token()
        title = request.form.get('title', '').strip()
        category = request.form.get('category', '').strip()
        file_type = request.form.get('file_type', 'image')
        caption = request.form.get('caption', '').strip()
        is_published = 1 if request.form.get('is_published') else 0

        file_obj = request.files.get('media_file')
        file_path = save_uploaded_file(file_obj, 'gallery')
        if not file_path:
            flash('Please upload a valid image or video file (Max 16MB).', 'danger')
            return render_template('admin/gallery_form.html', active_admin='gallery', item=None)

        db = get_db()
        db.execute('''
            INSERT INTO gallery (title, category, file_type, file_path, caption, is_published)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (title, category, file_type, file_path, caption, is_published))
        db.commit()

        flash(f"Gallery item '{title}' added successfully!", 'success')
        return redirect(url_for('admin_gallery'))

    return render_template('admin/gallery_form.html', active_admin='gallery', item=None)

@app.route('/admin/gallery/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def admin_gallery_edit(id):
    """Edit gallery item"""
    db = get_db()
    item = db.execute("SELECT * FROM gallery WHERE id = ?", (id,)).fetchone()
    if not item:
        flash('Gallery item not found.', 'danger')
        return redirect(url_for('admin_gallery'))

    if request.method == 'POST':
        verify_csrf_token()
        title = request.form.get('title', '').strip()
        category = request.form.get('category', '').strip()
        file_type = request.form.get('file_type', 'image')
        caption = request.form.get('caption', '').strip()
        is_published = 1 if request.form.get('is_published') else 0

        file_path = item['file_path']
        file_obj = request.files.get('media_file')
        new_file = save_uploaded_file(file_obj, 'gallery')
        if new_file:
            if file_path and file_path != new_file:
                delete_uploaded_file(file_path)
            file_path = new_file

        db.execute('''
            UPDATE gallery
            SET title = ?, category = ?, file_type = ?, file_path = ?, caption = ?, is_published = ?
            WHERE id = ?
        ''', (title, category, file_type, file_path, caption, is_published, id))
        db.commit()

        flash(f"Gallery item '{title}' updated successfully!", 'success')
        return redirect(url_for('admin_gallery'))

    return render_template('admin/gallery_form.html', active_admin='gallery', item=item)

@app.route('/admin/gallery/toggle/<int:id>', methods=['POST'])
@login_required
def admin_gallery_toggle(id):
    """Toggle publish/unpublish gallery item"""
    verify_csrf_token()
    db = get_db()
    item = db.execute("SELECT is_published, title FROM gallery WHERE id = ?", (id,)).fetchone()
    if item:
        new_status = 0 if item['is_published'] else 1
        db.execute("UPDATE gallery SET is_published = ? WHERE id = ?", (new_status, id))
        db.commit()
        state_str = "published" if new_status else "unpublished"
        flash(f"Gallery media '{item['title']}' is now {state_str}.", 'info')
    return redirect(url_for('admin_gallery'))

@app.route('/admin/gallery/delete/<int:id>', methods=['POST'])
@login_required
def admin_gallery_delete(id):
    """Delete gallery item"""
    verify_csrf_token()
    db = get_db()
    item = db.execute("SELECT file_path FROM gallery WHERE id = ?", (id,)).fetchone()
    if item and item['file_path']:
        delete_uploaded_file(item['file_path'])
    db.execute("DELETE FROM gallery WHERE id = ?", (id,))
    db.commit()
    flash('Gallery media deleted successfully.', 'success')
    return redirect(url_for('admin_gallery'))

# --- Certificates Management Routes ---

@app.route('/admin/certificates')
@login_required
def admin_certificates():
    """List certificates"""
    db = get_db()
    certs = db.execute("SELECT * FROM certificates ORDER BY id DESC").fetchall()
    return render_template('admin/certificates_list.html', active_admin='certificates', certificates=certs)

@app.route('/admin/certificates/add', methods=['GET', 'POST'])
@login_required
def admin_certificate_add():
    """Add a genuine certificate"""
    if request.method == 'POST':
        verify_csrf_token()
        title = request.form.get('title', '').strip()
        cert_number = request.form.get('cert_number', '').strip()
        issuing_authority = request.form.get('issuing_authority', '').strip()
        issue_date = request.form.get('issue_date', '').strip()
        description = request.form.get('description', '').strip()
        is_published = 1 if request.form.get('is_published') else 0

        file_obj = request.files.get('cert_file')
        file_path = save_uploaded_file(file_obj, 'certificates', {'pdf', 'png', 'jpg', 'jpeg', 'webp'}) or 'certificates/udyam_badge.svg'

        db = get_db()
        db.execute('''
            INSERT INTO certificates (title, cert_number, issuing_authority, issue_date, file_path, description, is_published)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (title, cert_number, issuing_authority, issue_date, file_path, description, is_published))
        db.commit()

        flash(f"Certificate '{title}' added successfully!", 'success')
        return redirect(url_for('admin_certificates'))

    return render_template('admin/certificate_form.html', active_admin='certificates', cert=None)

@app.route('/admin/certificates/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def admin_certificate_edit(id):
    """Edit certificate"""
    db = get_db()
    cert = db.execute("SELECT * FROM certificates WHERE id = ?", (id,)).fetchone()
    if not cert:
        flash('Certificate not found.', 'danger')
        return redirect(url_for('admin_certificates'))

    if request.method == 'POST':
        verify_csrf_token()
        title = request.form.get('title', '').strip()
        cert_number = request.form.get('cert_number', '').strip()
        issuing_authority = request.form.get('issuing_authority', '').strip()
        issue_date = request.form.get('issue_date', '').strip()
        description = request.form.get('description', '').strip()
        is_published = 1 if request.form.get('is_published') else 0

        file_path = cert['file_path']
        file_obj = request.files.get('cert_file')
        new_file = save_uploaded_file(file_obj, 'certificates', {'pdf', 'png', 'jpg', 'jpeg', 'webp'})
        if new_file:
            if file_path and file_path != new_file:
                delete_uploaded_file(file_path)
            file_path = new_file

        db.execute('''
            UPDATE certificates
            SET title = ?, cert_number = ?, issuing_authority = ?, issue_date = ?, file_path = ?, description = ?, is_published = ?
            WHERE id = ?
        ''', (title, cert_number, issuing_authority, issue_date, file_path, description, is_published, id))
        db.commit()

        flash(f"Certificate '{title}' updated successfully!", 'success')
        return redirect(url_for('admin_certificates'))

    return render_template('admin/certificate_form.html', active_admin='certificates', cert=cert)

@app.route('/admin/certificates/delete/<int:id>', methods=['POST'])
@login_required
def admin_certificate_delete(id):
    """Delete certificate"""
    verify_csrf_token()
    db = get_db()
    cert = db.execute("SELECT file_path FROM certificates WHERE id = ?", (id,)).fetchone()
    if cert and cert['file_path']:
        delete_uploaded_file(cert['file_path'])
    db.execute("DELETE FROM certificates WHERE id = ?", (id,))
    db.commit()
    flash('Certificate deleted successfully.', 'success')
    return redirect(url_for('admin_certificates'))

# --- News and Events Management Routes ---

@app.route('/admin/news')
@login_required
def admin_news():
    """List news milestones"""
    db = get_db()
    news_list = db.execute("SELECT * FROM news_items ORDER BY id DESC").fetchall()
    return render_template('admin/news_list.html', active_admin='news', news=news_list)

@app.route('/admin/news/add', methods=['GET', 'POST'])
@login_required
def admin_news_add():
    """Add a new milestone"""
    if request.method == 'POST':
        verify_csrf_token()
        title = request.form.get('title', '').strip()
        category = request.form.get('category', '').strip()
        date_display = request.form.get('date_display', '').strip()
        summary = request.form.get('summary', '').strip()
        content = request.form.get('content', '').strip()
        is_published = 1 if request.form.get('is_published') else 0

        file_obj = request.files.get('event_image')
        image_path = save_uploaded_file(file_obj, 'news') or 'factory/milestone_placeholder.svg'

        db = get_db()
        db.execute('''
            INSERT INTO news_items (title, category, summary, content, date_display, image, is_real, is_published)
            VALUES (?, ?, ?, ?, ?, ?, 1, ?)
        ''', (title, category, summary, content, date_display, image_path, is_published))
        db.commit()

        flash(f"Milestone '{title}' added successfully!", 'success')
        return redirect(url_for('admin_news'))

    return render_template('admin/news_form.html', active_admin='news', item=None)

@app.route('/admin/news/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def admin_news_edit(id):
    """Edit news milestone"""
    db = get_db()
    item = db.execute("SELECT * FROM news_items WHERE id = ?", (id,)).fetchone()
    if not item:
        flash('News item not found.', 'danger')
        return redirect(url_for('admin_news'))

    if request.method == 'POST':
        verify_csrf_token()
        title = request.form.get('title', '').strip()
        category = request.form.get('category', '').strip()
        date_display = request.form.get('date_display', '').strip()
        summary = request.form.get('summary', '').strip()
        content = request.form.get('content', '').strip()
        is_published = 1 if request.form.get('is_published') else 0

        image_path = item['image']
        file_obj = request.files.get('event_image')
        new_image = save_uploaded_file(file_obj, 'news')
        if new_image:
            if image_path and image_path != new_image:
                delete_uploaded_file(image_path)
            image_path = new_image

        db.execute('''
            UPDATE news_items
            SET title = ?, category = ?, summary = ?, content = ?, date_display = ?, image = ?, is_published = ?
            WHERE id = ?
        ''', (title, category, summary, content, date_display, image_path, is_published, id))
        db.commit()

        flash(f"Milestone '{title}' updated successfully!", 'success')
        return redirect(url_for('admin_news'))

    return render_template('admin/news_form.html', active_admin='news', item=item)

@app.route('/admin/news/toggle/<int:id>', methods=['POST'])
@login_required
def admin_news_toggle(id):
    """Toggle publish/unpublish news"""
    verify_csrf_token()
    db = get_db()
    item = db.execute("SELECT is_published, title FROM news_items WHERE id = ?", (id,)).fetchone()
    if item:
        new_status = 0 if item['is_published'] else 1
        db.execute("UPDATE news_items SET is_published = ? WHERE id = ?", (new_status, id))
        db.commit()
        state_str = "published" if new_status else "unpublished"
        flash(f"Milestone '{item['title']}' is now {state_str}.", 'info')
    return redirect(url_for('admin_news'))

@app.route('/admin/news/delete/<int:id>', methods=['POST'])
@login_required
def admin_news_delete(id):
    """Delete news milestone"""
    verify_csrf_token()
    db = get_db()
    item = db.execute("SELECT image FROM news_items WHERE id = ?", (id,)).fetchone()
    if item and item['image']:
        delete_uploaded_file(item['image'])
    db.execute("DELETE FROM news_items WHERE id = ?", (id,))
    db.commit()
    flash('News milestone deleted successfully.', 'success')
    return redirect(url_for('admin_news'))

# --- Enquiry Management Routes ---

@app.route('/admin/enquiries')
@login_required
def admin_enquiries():
    """List customer RFQs and enquiries with status filtering"""
    status_filter = request.args.get('status', '').strip()
    db = get_db()

    total_count = db.execute("SELECT COUNT(*) as c FROM enquiries").fetchone()['c']
    new_count = db.execute("SELECT COUNT(*) as c FROM enquiries WHERE status = 'New'").fetchone()['c']

    if status_filter in ['New', 'Contacted', 'Completed']:
        enquiries_list = db.execute(
            "SELECT * FROM enquiries WHERE status = ? ORDER BY id DESC", (status_filter,)
        ).fetchall()
    else:
        enquiries_list = db.execute("SELECT * FROM enquiries ORDER BY id DESC").fetchall()

    return render_template(
        'admin/enquiries_list.html',
        active_admin='enquiries',
        enquiries=enquiries_list,
        current_status=status_filter,
        total_count=total_count,
        new_count=new_count
    )

@app.route('/admin/enquiries/<int:id>')
@login_required
def admin_enquiry_detail(id):
    """View full customer enquiry details"""
    db = get_db()
    enquiry = db.execute("SELECT * FROM enquiries WHERE id = ?", (id,)).fetchone()
    if not enquiry:
        flash('Enquiry not found.', 'danger')
        return redirect(url_for('admin_enquiries'))

    return render_template('admin/enquiry_detail.html', active_admin='enquiries', enquiry=enquiry)

@app.route('/admin/enquiries/status/<int:id>', methods=['POST'])
@login_required
def admin_enquiry_status(id):
    """Update status of enquiry (New, Contacted, Completed)"""
    verify_csrf_token()
    new_status = request.form.get('status', '').strip()
    if new_status in ['New', 'Contacted', 'Completed']:
        db = get_db()
        db.execute("UPDATE enquiries SET status = ? WHERE id = ?", (new_status, id))
        db.commit()
        flash(f"Enquiry #{id} status updated to '{new_status}'.", 'success')
    return redirect(request.referrer or url_for('admin_enquiries'))

@app.route('/admin/enquiries/delete/<int:id>', methods=['POST'])
@login_required
def admin_enquiry_delete(id):
    """Delete an enquiry record with confirmation"""
    verify_csrf_token()
    db = get_db()
    db.execute("DELETE FROM enquiries WHERE id = ?", (id,))
    db.commit()
    flash(f"Enquiry #{id} was deleted successfully.", 'success')
    return redirect(url_for('admin_enquiries'))

# --- Custom Safe Error Handlers (No internal paths or traces leaked) ---
@app.errorhandler(400)
def bad_request_error(e):
    return render_template('errors/400.html'), 400

@app.errorhandler(403)
def forbidden_error(e):
    return render_template('errors/403.html'), 403

@app.errorhandler(404)
def not_found_error(e):
    return render_template('errors/404.html'), 404

@app.errorhandler(413)
def file_too_large_error(e):
    return render_template('errors/413.html'), 413

@app.errorhandler(500)
def internal_server_error(e):
    app.logger.error(f"Internal Server Error: {e}")
    return render_template('errors/500.html'), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=app.debug)
