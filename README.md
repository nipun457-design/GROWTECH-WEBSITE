# GROWTECH ENGINEERS — Official Corporate Website & Owner Admin Dashboard

Official corporate website and private owner administration dashboard for **GROWTECH ENGINEERS (GTE – Let's Get Growing)**, an industrial manufacturing company specializing in precision machine components, jigs & fixtures, receiving gauges, tandem press tools, hydraulic presses, trolleys, racks, and plant engineering solutions located in Pachgaon, Manesar, Gurugram.

---

## 1. Verified Company & Branding Information

- **Company Name:** GROWTECH ENGINEERS
- **Brand Identity & Tagline:** **GTE – Let's Get Growing** (Deep Industrial Blue gear `#1b3f66` & Precision Upward Green arrow `#5c9e2b`).
- **Proprietor:** Mr. Naresh Kumar (22+ Years of Hands-on Engineering and Toolroom Experience).
- **Date of Establishment:** September 2023 (as stated in official company profile).
- **Official Email:** `growtechengineers911@gmail.com`
- **Direct Contact Phone:** `+91-9991535590` (Mr. Naresh Kumar, Proprietor)
- **WhatsApp Support:** Direct working WhatsApp link (+91-9991535590) with pre-filled enquiry text.
- **Instagram Channel:** `@growtechengineers_911`
- **Factory Location:** Main Market, Fazalwas, Tauru Road, Pachgaon, Manesar, Gurugram, Haryana – 122413, India.
- **Government Registrations:**
  - **Udyam Registration No.:** `UDYAM-HR-05-0093212` (Micro Enterprise, Ministry of MSME, Govt. of India).
  - **GSTIN:** `06BIYPK7127F1ZV`
  - **NIC Code:** `28221` (Manufacture of machine tools for turning, drilling, milling, shaping, grinding).
  - *Integrity Note:* Only genuine government records are displayed; strictly no invented ISO certifications.

---

## 2. Production Architecture & Technology Stack

### Technology Stack
- **Backend Framework:** Python Flask 3.1+
- **Production WSGI Server:** Gunicorn 21+ (`--workers 2 --threads 4 --timeout 120`)
- **Database Engine:** Dual Engine Support (`db.py`):
  - **Local Development:** SQLite 3 (`growtech.db`).
  - **Production:** Render Managed PostgreSQL (via `DATABASE_URL`).
- **Persistent Storage:** Render Persistent Disk mounted at `/var/data/uploads` (or local `static/uploads/`).
- **Frontend:** HTML5, CSS3, JavaScript (ES6), Bootstrap 5.3 (CDN), Bootstrap Icons.
- **Security & Session Protection:**
  - Werkzeug PBKDF2:SHA256 password hashing.
  - Per-session cryptographic CSRF tokens on all state-changing endpoints.
  - `HttpOnly`, `SameSite=Lax`, and `Secure` cookie flags.
  - Upload file size limit capped at 16MB (`MAX_CONTENT_LENGTH`).
  - Strict file extension whitelisting (`.png`, `.jpg`, `.jpeg`, `.webp`, `.svg`, `.pdf`, `.mp4`, `.webm`) and executable file blocking (`.exe`, `.sh`, `.php`, `.py`, `.bat`).
  - Safe filename generation via 12-char randomized hex UUID + UNIX timestamp.
  - Strict path traversal prevention on media endpoints (`/static/uploads/`, `/uploads/`).
  - Custom safe error pages (400, 403, 404, 413, 500) preventing stack traces or internal paths from leaking to visitors.
  - Health check endpoint at `/api/health`.

---

## 3. Public Website Integration

All public pages query live content from the database:
- **Homepage (`/`):** Dynamic featured products, real factory photographs, genuine client logos (Toyota Boshoku, Nitto, AtMa, Onassis Auto, NSSI, SE, SFC, Wahi Sons, Hi-Lex Act), machinery showcase, and quick enquiry form.
- **Company Page (`/company`):** Real-time reflection of company background, proprietor profile, vision, mission, factory infrastructure specifications (area, power backup, technical team), and plant equipment inventory.
- **Products Catalog (`/products`):** Dynamically filters and displays published products across all 6 core categories. Unpublished products remain hidden from visitors.
- **News & Milestones (`/news`):** Chronological gallery of verified company achievements and infrastructure expansions.
- **Contact Us (`/contact`):** Full contact coordinates, interactive directions, and direct RFQ form submission with database storage and server-side validation.

---

## 4. Private Owner Admin Dashboard

A secure, private administration portal built exclusively for the business owner (Mr. Naresh Kumar) to manage website content dynamically without touching source code.

- **Admin Login URL:** `http://127.0.0.1:5000/admin/login`
- **Zero Public Registration:** Strictly no public registration or customer login.
- **Route Guarding:** All `/admin/*` routes require authenticated session via `@login_required`.
- **Content Management Modules:**
  1. **Overview Dashboard (`/admin/dashboard`):** Real-time metrics for products, RFQs, gallery assets, and milestones.
  2. **Product Management (`/admin/products`):** Add, edit, delete, publish/unpublish toggle, multi-image upload, specifications, video URL.
  3. **Company Content Management (`/admin/company`):** Dynamic update of company profile, vision, mission, factory area, technical team, power backup.
  4. **Gallery Management (`/admin/gallery`):** Manage factory, machinery, product, and project photos/videos.
  5. **Certificates Management (`/admin/certificates`):** Genuine government and technical compliance documents (Udyam, GSTIN, calibration records).
  6. **News & Events Management (`/admin/news`):** Company milestones and announcements.
  7. **Customer Enquiry Management (`/admin/enquiries`):** Status filtering (`New`, `Contacted`, `Completed`), complete RFQ details viewer, WhatsApp/Email quick replies.

---

## 5. Database Schema & Migration

Database abstraction module: [db.py](file:///c:/Users/nipun/OneDrive/Desktop/GROWTECH-WEBSITE/db.py).
Supports both SQLite (`growtech.db`) and PostgreSQL (`DATABASE_URL`).

| Table | Purpose |
| :--- | :--- |
| `users` | Admin user credentials with PBKDF2:SHA256 password hash, role, and last login. |
| `enquiries` | Customer RFQ submissions with contact details, requirement category, message, IP, and status. |
| `products` | Product catalog with category, slug, features JSON, applications JSON, and publication state. |
| `product_images` | Multiple photographs per product with caption and primary image flag. |
| `company_content` | Key-value store for dynamic company profile, vision, mission, and plant facilities. |
| `gallery` | Factory, machinery, and project media items (images & videos). |
| `certificates` | Genuine government and technical compliance certificates. |
| `news_items` | Verified company milestones and events. |

### Database Tools
- **Initialize Schema & Seed Initial Content:**
  ```powershell
  python migrate_phase2.py
  ```
- **Backup All Tables to JSON:**
  ```powershell
  python migrate_data.py --backup
  ```
- **Restore Data from Backup:**
  ```powershell
  python migrate_data.py --restore backups/your_backup_file.json
  ```
- **Migrate Local SQLite Data to PostgreSQL:**
  ```powershell
  python migrate_data.py --sqlite-to-postgres
  ```

---

## 6. How to Run & Verify Locally

### Step 1: Install Dependencies
```powershell
pip install -r requirements.txt
```

### Step 2: Run Full Automated Test Suite (33 Tests)
```powershell
python -m unittest test_app.py test_phase2.py test_production.py test_supabase_storage.py
```
*(All 33 tests pass: 7 public regression tests + 11 admin management tests + 8 production readiness tests + 7 Supabase storage & ephemeral filesystem resilience tests).*

### Step 3: Run the Local Development Server
```powershell
python app.py
```

### Step 4: Access in Web Browser
- **Public Website:** [http://127.0.0.1:5000/](http://127.0.0.1:5000/)
- **Health Check:** [http://127.0.0.1:5000/api/health](http://127.0.0.1:5000/api/health)
- **Admin Dashboard:** [http://127.0.0.1:5000/admin/login](http://127.0.0.1:5000/admin/login)

---

## 7. Production Deployment (100% Free ₹0 Architecture)

The application is engineered for zero-cost production hosting on:
- **Render Free Web Service** (Python 3, Gunicorn WSGI, TLS/HTTPS, ₹0/month)
- **Supabase Free PostgreSQL** (Managed database via `DATABASE_URL`, ₹0/month)
- **Supabase Free Storage** (Cloud uploads in `growtech-uploads` bucket, permanent CDN URLs, ₹0/month)

For complete step-by-step setup instructions, refer to:
👉 **[DEPLOYMENT_GUIDE.md](file:///c:/Users/nipun/OneDrive/Desktop/GROWTECH-WEBSITE/DEPLOYMENT_GUIDE.md)**
