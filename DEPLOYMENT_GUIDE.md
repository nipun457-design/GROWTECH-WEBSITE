# GROWTECH ENGINEERS — Production Deployment Guide (Render)

This guide documents the complete procedure for deploying the **GROWTECH ENGINEERS** corporate web application to [Render](https://render.com) using a production-grade architecture:
- **Render Web Service:** Python Flask with Gunicorn WSGI server.
- **Render PostgreSQL:** Managed relational database with automatic backups.
- **Render Persistent Disk:** Permanent persistent storage mounted at `/var/data/uploads` for media, documents, and certificates.
- **HTTPS & SSL:** Managed TLS encryption provided automatically by Render.
- **Private Owner Admin Portal:** Secure `/admin` dashboard access for Mr. Naresh Kumar.

---

## Architecture Overview

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
                                  |  Render Web Service (Linux)        |
                                  |  - Gunicorn WSGI (2 w / 4 th)      |
                                  |  - Flask 3.x Production App        |
                                  |  - Health: /api/health             |
                                  +--------+------------------+--------+
                                           |                  |
                       (Persistent Storage)|                  |(DATABASE_URL)
                                           v                  v
                 +-------------------------+---+  +-----------+----------------------+
                 | Render Persistent Disk      |  | Render Managed PostgreSQL        |
                 | Mount: /var/data/uploads/   |  | Tables: users, products,          |
                 | - products/                 |  |         enquiries, gallery,       |
                 | - gallery/                  |  |         certificates, news        |
                 | - certificates/             |  +----------------------------------+
                 | - news/                     |
                 +-----------------------------+
```

---

## 1. Prerequisites

Before beginning the deployment:
1. A Git repository (e.g., GitHub, GitLab) containing the `GROWTECH-WEBSITE` project files.
2. Verify that `.gitignore` is present so that local SQLite databases (`growtech.db`), `.env` files, and temporary caches are **not** committed to version control.
3. A web browser to access the [Render Dashboard](https://dashboard.render.com).

---

## 2. Step 1: Create a Render Account

1. Navigate to **[https://render.com](https://render.com)**.
2. Click **Get Started** or **Sign In**.
3. Sign in using your GitHub account (recommended for seamless repository linking) or sign up using your corporate email (`growtechengineers911@gmail.com`).
4. Complete email verification if prompted.

---

## 3. Deployment Options

You can deploy to Render using either:
- **Option 1: Render Blueprint (Infrastructure-as-Code — Recommended):** Render reads `render.yaml` and provisions the Web Service, PostgreSQL database, persistent disk, and environment variables automatically.
- **Option 2: Manual Dashboard Setup:** Step-by-step creation via the Render Web UI.

### Note on Render Plans & Persistent Disks
- **Starter Plan (Full Production):** Render requires the Web Service to be on the `Starter` plan ($7/month) to attach a persistent disk (`/var/data/uploads`). This ensures product photos, certificates, and media uploaded by the owner persist across application updates, re-deploys, and container restarts.
- **Free Tier (Evaluation / Demo):** If using Render's Free tier, the PostgreSQL database is free (for 30 days), but persistent disks cannot be attached. Uploaded files will be stored in `static/uploads` within the container (ephemeral). In `render.yaml`, the Web Service is configured with `plan: starter` and PostgreSQL with `plan: free`.

---

## 4. Option 1: One-Click Deploy via Render Blueprint (Recommended)

1. Push your repository to GitHub.
2. In the Render Dashboard, click **New +** in the top-right corner and select **Blueprint**.
3. Select your `growtech-website` repository.
4. Render will parse `render.yaml` and display the resources to be created:
   - **growtech-engineers-web** (Web Service, Python 3, Gunicorn, Starter plan)
   - **growtech-uploads** (Persistent Disk, 1 GB mounted at `/var/data/uploads`)
   - **growtech-db** (Managed PostgreSQL database, Free plan)
5. Review the plan and click **Apply**.
6. Render will automatically build the service, run `migrate_phase2.py` to create tables, and start Gunicorn.
7. Proceed to **Step 8: Initial Admin Account Setup**.

---

## 5. Option 2: Manual Dashboard Setup

Ensure your local project code is pushed to your private or organization GitHub repository:
```bash
git init
git add .
git commit -m "Production release: GROWTECH ENGINEERS Corporate Platform"
git remote add origin https://github.com/<your-org-or-user>/growtech-website.git
git branch -M main
git push -u origin main
```

---

## 4. Step 3: Create the Render PostgreSQL Database

1. In the Render Dashboard, click **New +** in the top-right corner and select **PostgreSQL**.
2. Configure the database details:
   - **Name:** `growtech-db`
   - **Database:** `growtech`
   - **User:** `growtech_user`
   - **Region:** `Singapore` (recommended for low latency in India) or `Frankfurt` / `Oregon`.
   - **PostgreSQL Version:** `16` (Default)
   - **Plan:** `Free` (or `Starter` for high-availability production workloads).
3. Click **Create Database**.
4. Once provisioned (typically 1–2 minutes), find the **Connections** panel:
   - Copy the **Internal Database URL** (e.g., `postgresql://growtech_user:password@dpg-.../growtech`).
   - *Note:* Render web services in the same region communicate securely over the internal network via the Internal Database URL.

---

## 5. Step 4: Create the Render Web Service

1. In the Render Dashboard, click **New +** and select **Web Service**.
2. Select **Build and deploy from a Git repository** and connect your `growtech-website` repository.
3. Configure the Web Service settings:
   - **Name:** `growtech-engineers-web`
   - **Language:** `Python 3`
   - **Region:** Same region as your database (`Singapore`).
   - **Branch:** `main`
   - **Build Command:**
     ```bash
     pip install -r requirements.txt && python migrate_phase2.py
     ```
   - **Start Command:**
     ```bash
     gunicorn app:app --workers 2 --threads 4 --timeout 120
     ```
   - **Plan:** `Free` (or `Starter` if attaching a persistent disk).

---

## 6. Step 5: Configure Persistent Disk Storage

Render allows attaching a persistent disk to ensure uploaded product photos, machinery videos, and compliance documents are never lost upon code updates or restarts:

1. In the Web Service settings page, scroll down to the **Disks** section.
2. Click **Add Disk**:
   - **Name:** `growtech-uploads`
   - **Mount Path:** `/var/data/uploads`
   - **Size:** `1 GB` (or larger depending on planned catalogue volume).
3. Save the disk configuration.

---

## 7. Step 6: Configure Environment Variables

In the Web Service settings, navigate to the **Environment** tab and add the following variables:

| Key | Recommended Production Value | Description |
| :--- | :--- | :--- |
| `FLASK_ENV` | `production` | Enables production mode |
| `FLASK_DEBUG` | `false` | Disables debug mode and tracebacks |
| `SECRET_KEY` | *(Click "Generate" in Render or generate a random 64-char key)* | Cryptographic session signing key |
| `DATABASE_URL` | *(Paste Internal Database URL from Step 3)* | Connection string to Render PostgreSQL |
| `UPLOAD_FOLDER` | `/var/data/uploads` | Path to the persistent disk storage |
| `SESSION_COOKIE_SECURE` | `true` | Enforces HTTPS-only cookies |
| `SESSION_COOKIE_HTTPONLY` | `true` | Protects cookies from client-side scripts |
| `SESSION_COOKIE_SAMESITE` | `Lax` | Mitigates CSRF token hijacking |
| `ADMIN_USERNAME` | `admin` | Initial owner account username |
| `ADMIN_PASSWORD` | *(Enter a secure production password, min 12 chars)* | Master password for Mr. Naresh Kumar |

*Security Warning:* Never reuse the default development password. Enter a strong, private password known only to the business owner.

---

## 8. Step 7: Automatic Deployment & Schema Initialization

1. Click **Create Web Service** (or **Manual Deploy > Deploy latest commit**).
2. Render will execute:
   - `pip install -r requirements.txt`
   - `python migrate_phase2.py` (which connects to PostgreSQL, creates all 8 relational tables with `SERIAL PRIMARY KEY`, and seeds initial verified products, company profile information, gallery items, and milestones).
3. Once the build finishes, verify the logs display:
   ```
   Database migration completed successfully.
   [INFO] Starting gunicorn 21.x.x
   [INFO] Listening at: http://0.0.0.0:10000
   ```
4. Access the health check endpoint in your browser:
   `https://growtech-engineers-web.onrender.com/api/health`
   Should return HTTP 200:
   ```json
   {
     "status": "healthy",
     "service": "GROWTECH ENGINEERS Corporate Web Application",
     "database": "connected",
     "environment": "production"
   }
   ```

---

## 9. Step 8: Initial Admin Account Setup / Password Reset

To provision or reset the owner account directly on the live Render environment:

### Method A: Via Render Shell (Recommended)
1. In the Render Dashboard, open the `growtech-engineers-web` service.
2. Click the **Shell** tab on the left menu.
3. Run the interactive account provisioner:
   ```bash
   python create_admin.py --interactive
   ```
4. Enter the administrator username (e.g. `admin`) and set the owner's private password (minimum 8 characters; password input will remain hidden).
5. Output will confirm:
   `Admin account 'admin' updated/reset successfully.`

### Method B: Password Reset Utility
If the owner ever needs to reset credentials later:
```bash
python create_admin.py --username admin --password "NewSecurePassword123!" --reset-password
```

---

## 10. Step 9: Migrating Existing Local Data to Production (Optional)

If you have test enquiries or content in your local `growtech.db` SQLite database that you wish to transfer to Render PostgreSQL:

1. **Create a local JSON backup:**
   ```powershell
   python migrate_data.py --backup
   ```
   *(Saves to `backups/growtech_backup_<timestamp>.json`).*
2. **Transfer to production:**
   Set the Render PostgreSQL connection string in your local PowerShell session temporarily and run the direct migrator:
   ```powershell
   $env:DATABASE_URL="postgresql://growtech_user:<password>@<external-host>.render.com/growtech"
   python migrate_data.py --sqlite-to-postgres
   Remove-Item env:DATABASE_URL
   ```
   *(All existing enquiry records, products, gallery media, and company keys will be imported safely without duplicates).*

---

## 11. Step 10: Connecting a Custom Domain (e.g., growtechengineers.com)

1. In the Render Web Service dashboard, navigate to **Settings > Custom Domains**.
2. Click **Add Custom Domain**.
3. Enter your domain: `growtechengineers.com` and `www.growtechengineers.com`.
4. Configure your DNS provider (e.g. GoDaddy, Namecheap, Cloudflare, Google Domains):
   - **For `www`:** Add a `CNAME` record pointing to your Render service address (e.g., `growtech-engineers-web.onrender.com`).
   - **For apex domain (`growtechengineers.com`):** Add an `A` record pointing to Render's IP address (shown in your Render dashboard).
5. Render will automatically issue and renew a free Let's Encrypt SSL certificate within a few minutes.

---

## 12. Verification & Smoke Testing Checklist

After deployment, perform these verification checks on the live site:
- [ ] **Homepage (`/`):** Logo, factory entrance hero image, capabilities, and customer logos load with HTTPS.
- [ ] **Company Page (`/company`):** Company background, proprietor profile, vision, mission, and equipment inventory load.
- [ ] **Products Catalog (`/products`):** Category filter tabs work and technical specifications appear.
- [ ] **Enquiry Submission (`/contact`):** Submit a test RFQ; verify success alert and check that it appears in `/admin/enquiries`.
- [ ] **Admin Login (`/admin/login`):** Log in using the owner credentials created in Step 8.
- [ ] **Unauthorized Access:** Open an Incognito window and visit `/admin/products`; verify redirection to `/admin/login`.
- [ ] **Health Endpoint (`/api/health`):** Returns `"status": "healthy"` and `"database": "connected"`.
- [ ] **404 Page (`/any-invalid-url`):** Renders branded industrial error page without stack traces.
