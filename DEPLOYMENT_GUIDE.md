# GROWTECH ENGINEERS — Production Deployment Guide (100% Free ₹0 Architecture)

This guide documents the complete procedure for deploying the **GROWTECH ENGINEERS** corporate web platform with a **strict budget of ₹0 / month**:
- **Render Free Web Service:** Python Flask with Gunicorn WSGI server (Free tier, HTTPS included, zero hosting fee).
- **Supabase Free PostgreSQL:** High-performance managed PostgreSQL database (Free tier, 500 MB storage, zero database fee).
- **Supabase Free Storage:** Permanent cloud object storage for admin-uploaded product photos, gallery media, compliance documents, and news milestones (Free tier, 1 GB storage, public CDN URLs, zero storage fee).
- **Local Development Parity:** SQLite (`growtech.db`) and local uploads (`static/uploads/`) remain default for local offline work.

---

## ₹0 Architecture Overview

```
                                  +------------------------------------+
                                  |         Internet Visitors          |
                                  +-----------------+------------------+
                                                    | (HTTPS)
                                                    v
                                  +-----------------+------------------+
                                  |    Render Managed TLS / CDN        |
                                  +-----------------+------------------+
                                                    |
                                                    v
                                  +-----------------+------------------+
                                  |  Render Free Web Service (Linux)   |
                                  |  - Gunicorn WSGI (2 w / 4 th)      |
                                  |  - Flask 3.x Production App        |
                                  |  - Plan: FREE (₹0/mo)              |
                                  |  - Health: /api/health             |
                                  +--------+------------------+--------+
                                           |                  |
           (Direct Cloud Image URLs / CDN) |                  |(DATABASE_URL)
                                           v                  v
                 +-------------------------+---+  +-----------+----------------------+
                 | Supabase Free Storage       |  | Supabase Free PostgreSQL         |
                 | Bucket: growtech-uploads    |  | Plan: FREE (₹0/mo)               |
                 | - products/                 |  | Tables: users, products,          |
                 | - gallery/                  |  |         enquiries, gallery,       |
                 | - certificates/             |  |         certificates, news        |
                 | - news/                     |  +----------------------------------+
                 +-----------------------------+
```

---

## 1. Prerequisites

1. A Git repository on GitHub containing the `GROWTECH-WEBSITE` project.
2. A free [Supabase](https://supabase.com) account (no credit card required).
3. A free [Render](https://render.com) account (no credit card required for free web services).

---

## 2. Step 1: Set Up Supabase (Database & Storage)

### A. Create a New Supabase Project
1. Go to **[https://supabase.com](https://supabase.com)** and sign in.
2. Click **New Project**.
3. Fill in the details:
   - **Name:** `growtech-engineers`
   - **Database Password:** Enter a strong password (save this securely).
   - **Region:** `Singapore` (recommended for lowest latency in India) or closest to your audience.
   - **Pricing Plan:** **Free Tier (₹0 / month)**.
4. Click **Create new project** and wait 1–2 minutes for provisioning.

### B. Copy the PostgreSQL Connection String (`DATABASE_URL`)
1. In your Supabase project dashboard, click **Project Settings** (gear icon at the bottom of the left sidebar).
2. Click **Database**.
3. Scroll to **Connection string** and select **URI**:
   - Choose **Transaction pooler (Port 6543)** or **Direct (Port 5432)**.
   - The connection string looks like:
     ```
     postgresql://postgres.[project-ref]:[YOUR-PASSWORD]@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres
     ```
   - Replace `[YOUR-PASSWORD]` with the database password you chose in Step A.
   - This value will be your `DATABASE_URL` environment variable.

### C. Create the Public Storage Bucket (`growtech-uploads`)
1. Click **Storage** in the left sidebar menu.
2. Click **New bucket**.
3. Configure the bucket:
   - **Bucket Name:** `growtech-uploads`
   - **Public bucket:** **Toggle ON (Yes)** *(Required so website visitors can view product photos and gallery media).*
4. Click **Save**.

### D. Copy API Credentials (`SUPABASE_URL` and `SUPABASE_KEY`)
1. Navigate to **Project Settings > API**.
2. Under **Project URL**, copy the URL (e.g. `https://[project-ref].supabase.co`).
   - This is your `SUPABASE_URL`.
3. Under **Project API keys**, find the **service_role** key (click "Reveal" to copy).
   - *Security Note:* The `service_role` key is strictly kept in Render environment variables on the backend server. It is **never** sent to the client browser or included in frontend templates.
   - This is your `SUPABASE_KEY` (or `SUPABASE_SERVICE_ROLE_KEY`).

---

## 3. Step 2: Deploy to Render Free Web Service

You can deploy using either the Blueprint (`render.yaml`) or manual configuration:

### Option A: One-Click Deploy via Render Blueprint (Recommended)
1. Push your latest code to GitHub (`main` branch).
2. Go to the [Render Dashboard](https://dashboard.render.com).
3. Click **New +** in the top right and select **Blueprint**.
4. Select your `growtech-website` repository.
5. Render reads `render.yaml` and displays:
   - **Service:** `growtech-engineers-web` (Web Service, Python 3, Free Plan, ₹0/mo).
   - **Persistent Disk:** *None* (Persistent storage is handled by Supabase Storage).
   - **Databases:** *None* (PostgreSQL is hosted on Supabase).
6. Under Environment Variables, paste the values:
   - `DATABASE_URL`: Your Supabase PostgreSQL URI from Step 2B.
   - `SUPABASE_URL`: Your Supabase Project URL from Step 2D.
   - `SUPABASE_KEY`: Your Supabase Service Role key from Step 2D.
7. Click **Apply**.

---

### Option B: Manual Web Service Setup on Render
1. In Render Dashboard, click **New + > Web Service**.
2. Select **Build and deploy from a Git repository** and connect your repository.
3. Configure settings:
   - **Name:** `growtech-engineers-web`
   - **Language:** `Python 3`
   - **Region:** `Singapore` (or match Supabase region)
   - **Branch:** `main`
   - **Build Command:**
     ```bash
     pip install -r requirements.txt && python migrate_phase2.py
     ```
   - **Start Command:**
     ```bash
     gunicorn app:app --workers 2 --threads 4 --timeout 120
     ```
   - **Plan:** **Free (₹0 / month)**
4. In the **Environment** tab, add the environment variables:

| Key | Recommended Production Value | Description |
| :--- | :--- | :--- |
| `FLASK_ENV` | `production` | Production mode |
| `FLASK_DEBUG` | `false` | Disables debug mode and traces |
| `SECRET_KEY` | *(Click "Generate" or enter random 64-char key)* | Session signing key |
| `DATABASE_URL` | `postgresql://postgres.[ref]:[pass]@[host]:6543/postgres` | Supabase PostgreSQL URI |
| `SUPABASE_URL` | `https://[project-ref].supabase.co` | Supabase Project REST API URL |
| `SUPABASE_KEY` | `eyJhbGciOi...` | Supabase Service Role API Key |
| `SUPABASE_BUCKET`| `growtech-uploads` | Public storage bucket name |
| `SESSION_COOKIE_SECURE` | `true` | Enforces HTTPS-only cookies |
| `SESSION_COOKIE_HTTPONLY` | `true` | Protects cookies from client scripts |
| `SESSION_COOKIE_SAMESITE` | `Lax` | Mitigates CSRF token hijacking |

5. Click **Create Web Service**.

---

## 4. Step 3: Verify Automated Migration & Health

During deployment, Render runs:
1. `pip install -r requirements.txt`
2. `python migrate_phase2.py`:
   - Connects to Supabase PostgreSQL.
   - Creates all tables (`users`, `products`, `product_images`, `company_content`, `gallery`, `certificates`, `news_items`, `enquiries`).
   - Seeds initial verified company information and products if empty.
3. Verify the deployment logs show:
   ```
   Database migration completed successfully.
   [INFO] Starting gunicorn 21.x.x
   [INFO] Listening at: http://0.0.0.0:10000
   ```
4. Test the health check endpoint in your browser:
   `https://growtech-engineers-web.onrender.com/api/health`
   Expected response (HTTP 200):
   ```json
   {
     "status": "healthy",
     "service": "GROWTECH ENGINEERS Corporate Web Application",
     "database": "connected",
     "environment": "production"
   }
   ```

---

## 5. Step 4: Provision Owner Admin Account

To create or reset the administrator password for Mr. Naresh Kumar on the live environment:

1. In the Render Dashboard, open `growtech-engineers-web`.
2. Click the **Shell** tab on the left.
3. Run the interactive account provisioner:
   ```bash
   python create_admin.py --interactive
   ```
4. Enter the administrator username (e.g., `admin`) and set a strong password (minimum 8 characters).
5. Output will confirm:
   `Admin account 'admin' updated/reset successfully.`

---

## 6. Step 5: Safe Media & Data Migration (Optional)

If you have existing test records or uploaded media in your local SQLite environment that you wish to transfer to production:

### Database Records Migration:
1. Create a local JSON backup:
   ```powershell
   python migrate_data.py --backup
   ```
2. Set `DATABASE_URL` in your local PowerShell session temporarily and run:
   ```powershell
   $env:DATABASE_URL="postgresql://postgres.[ref]:[pass]@[host]:6543/postgres"
   python migrate_data.py --sqlite-to-postgres
   Remove-Item env:DATABASE_URL
   ```

### Local Uploaded Files Migration to Supabase Storage:
1. Run a **safe simulation (dry-run)** first to inspect what would be migrated:
   ```powershell
   $env:SUPABASE_URL="https://[project-ref].supabase.co"
   $env:SUPABASE_KEY="[service_role_key]"
   python migrate_data.py --migrate-media-to-supabase --dry-run
   ```
2. When ready, run the actual migration (prompts for confirmation before uploading):
   ```powershell
   python migrate_data.py --migrate-media-to-supabase
   Remove-Item env:SUPABASE_URL
   Remove-Item env:SUPABASE_KEY
   ```
   *(Committed factory photos in `static/images/` are protected and never duplicated or altered).*

---

## 7. Step 6: Post-Deployment Verification Checklist

- [ ] **Homepage (`/`):** Logo, hero facility photo, machinery photos, and client logos load correctly via HTTPS.
- [ ] **Catalog (`/products`):** Products and category filters load with images.
- [ ] **RFQ Enquiry Form (`/contact`):** Submit a test RFQ; verify success flash alert and check that it appears in `/admin/enquiries`.
- [ ] **Admin Login (`/admin/login`):** Log in using owner credentials.
- [ ] **Upload Test (`/admin/products/add`):** Upload a new test product image; verify it uploads to Supabase Storage and displays with its Supabase public URL.
- [ ] **Delete Test (`/admin/products/delete/<id>`):** Delete the test product; verify that the Supabase Storage object is cleaned up.
- [ ] **Ephemeral Filesystem Resilience:** Even after Render spins down or restarts, uploaded images remain accessible from Supabase CDN without loss.
- [ ] **Cost Audit:** Confirm that both Render and Supabase dashboards show **₹0 / $0.00** billing.
