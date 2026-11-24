import os
import io
import json
import sqlite3
import unittest
from werkzeug.security import generate_password_hash, check_password_hash
from app import app, DATABASE, allowed_file, save_uploaded_file

class Phase2AdminDashboardTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'test-secret-key-phase2-growtech'
        self.client = app.test_client()

        # Connect to DB and ensure admin user exists
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Ensure admin user
        cursor.execute("SELECT * FROM users WHERE username = 'admin'")
        admin = cursor.fetchone()
        if not admin:
            pw_hash = generate_password_hash("Growtech@2024Secure!", method='pbkdf2:sha256')
            cursor.execute('''
                INSERT INTO users (username, password_hash, full_name, email, role)
                VALUES (?, ?, ?, ?, ?)
            ''', ('admin', pw_hash, 'Naresh Kumar', 'growtechengineers911@gmail.com', 'admin'))
            conn.commit()
        conn.close()

    def get_csrf_token(self):
        """Helper to get a valid CSRF token from the session"""
        with self.client.session_transaction() as sess:
            if '_csrf_token' not in sess:
                sess['_csrf_token'] = 'test_phase2_csrf_token_1234567890'
            return sess['_csrf_token']

    def login_admin(self, username='admin', password='Growtech@2024Secure!'):
        """Helper to perform authenticated admin login"""
        csrf = self.get_csrf_token()
        return self.client.post('/admin/login', data={
            'username': username,
            'password': password,
            'csrf_token': csrf
        }, follow_redirects=True)

    # =========================================================================
    # 1. AUTHENTICATION & ACCESS CONTROL TESTS
    # =========================================================================

    def test_unauthorized_access_protection(self):
        """Verify that all protected admin routes redirect to /admin/login when unauthenticated"""
        protected_routes = [
            '/admin',
            '/admin/dashboard',
            '/admin/products',
            '/admin/products/add',
            '/admin/company',
            '/admin/gallery',
            '/admin/gallery/add',
            '/admin/certificates',
            '/admin/certificates/add',
            '/admin/news',
            '/admin/news/add',
            '/admin/enquiries'
        ]
        for route in protected_routes:
            response = self.client.get(route, follow_redirects=False)
            self.assertEqual(
                response.status_code, 302,
                f"Unauthenticated access to {route} did not redirect! Status: {response.status_code}"
            )
            self.assertIn('/admin/login', response.headers.get('Location', ''))

    def test_admin_login_invalid_credentials(self):
        """Verify that invalid login attempts are rejected with error flash"""
        csrf = self.get_csrf_token()
        response = self.client.post('/admin/login', data={
            'username': 'admin',
            'password': 'WrongPassword123!',
            'csrf_token': csrf
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Invalid administrator credentials', response.data)

        # Check session does not have admin_user_id
        with self.client.session_transaction() as sess:
            self.assertNotIn('admin_user_id', sess)

    def test_admin_login_success_and_logout(self):
        """Verify valid admin login establishes session and logout clears it"""
        response = self.login_admin()
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Dashboard Overview', response.data)
        self.assertIn(b'Naresh Kumar', response.data)

        # Verify session is populated
        with self.client.session_transaction() as sess:
            self.assertEqual(sess.get('admin_username'), 'admin')
            self.assertEqual(sess.get('admin_role'), 'admin')

        # Test Logout
        logout_res = self.client.get('/admin/logout', follow_redirects=True)
        self.assertEqual(logout_res.status_code, 200)
        self.assertIn(b'You have been logged out securely', logout_res.data)

        # Verify session is cleared
        with self.client.session_transaction() as sess:
            self.assertNotIn('admin_user_id', sess)

    def test_csrf_protection_enforcement(self):
        """Verify that state-changing POST requests without CSRF token are aborted with 403 Forbidden"""
        self.login_admin()
        # Attempt to POST without CSRF token
        response = self.client.post('/admin/products/toggle/1', data={})
        self.assertEqual(response.status_code, 403)

    # =========================================================================
    # 2. PRODUCT MANAGEMENT TESTS
    # =========================================================================

    def test_product_crud_and_public_visibility(self):
        """Test full Product lifecycle: create, public visibility, toggle unpublish/publish, delete"""
        self.login_admin()
        csrf = self.get_csrf_token()

        unique_title = 'High-Precision Laser Inspection Fixture'
        category = 'Jigs & Fixtures'
        summary = 'Custom laser alignment fixture for automotive tubular assemblies.'
        description = 'Engineered for sub-millimeter GD&T inspection and robotic positioning.'
        features = 'Laser triangulation sensor mount\nSub-millimeter repeatability 0.005mm\nPneumatic clamp'
        applications = 'Tubular chassis inspection\nRobotic weld positioning'

        dummy_img = (io.BytesIO(b'Fake-JPEG-Content-Bytes-12345'), 'fixture_test.jpg')

        # 1. Add Product
        add_res = self.client.post('/admin/products/add', data={
            'title': unique_title,
            'category': category,
            'tag': 'Precision Tooling',
            'summary': summary,
            'description': description,
            'features': features,
            'applications': applications,
            'video_url': '',
            'status_note': 'In Active Production',
            'is_featured': '1',
            'is_published': '1',
            'primary_image': dummy_img,
            'csrf_token': csrf
        }, content_type='multipart/form-data', follow_redirects=True)

        self.assertEqual(add_res.status_code, 200)
        self.assertIn(b'added successfully', add_res.data)

        # Find product ID in database
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM products WHERE title = ?", (unique_title,))
        product = c.fetchone()
        conn.close()

        self.assertIsNotNone(product, "Product was not found in DB after creation")
        product_id = product['id']
        self.assertEqual(product['is_published'], 1)

        # 2. Verify product appears on public /products page
        pub_res = self.client.get('/products')
        self.assertEqual(pub_res.status_code, 200)
        self.assertIn(unique_title.encode('utf-8'), pub_res.data)

        # 3. Toggle product to UNPUBLISHED
        toggle_res = self.client.post(f'/admin/products/toggle/{product_id}', data={
            'csrf_token': csrf
        }, follow_redirects=True)
        self.assertEqual(toggle_res.status_code, 200)

        # Verify DB updated to is_published = 0
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute("SELECT is_published FROM products WHERE id = ?", (product_id,))
        status = c.fetchone()[0]
        conn.close()
        self.assertEqual(status, 0, "Product should be unpublished")

        # 4. Verify product is HIDDEN on public /products page
        pub_res2 = self.client.get('/products')
        self.assertEqual(pub_res2.status_code, 200)
        self.assertNotIn(unique_title.encode('utf-8'), pub_res2.data)

        # 5. Delete product
        del_res = self.client.post(f'/admin/products/delete/{product_id}', data={
            'csrf_token': csrf
        }, follow_redirects=True)
        self.assertEqual(del_res.status_code, 200)

        # Verify deleted from DB
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM products WHERE id = ?", (product_id,))
        count = c.fetchone()[0]
        conn.close()
        self.assertEqual(count, 0, "Product was not deleted from DB")

    # =========================================================================
    # 3. COMPANY CONTENT MANAGEMENT TESTS
    # =========================================================================

    def test_company_content_update_and_public_reflection(self):
        """Test updating company info via admin and verifying immediate reflection on public pages"""
        self.login_admin()
        csrf = self.get_csrf_token()

        new_slogan = "Pioneering Industrial Precision & Engineering Excellence"
        new_facilities = "12,500 sq. ft. State-of-the-art Industrial Unit"

        # Update via admin/company
        res = self.client.post('/admin/company', data={
            'company_name': 'GROWTECH ENGINEERS',
            'slogan': new_slogan,
            'tagline': "Let's Get Growing",
            'business': 'Manufacturing machine components, precision jigs, fixtures & press tools',
            'proprietor': 'Mr. Naresh Kumar',
            'proprietor_experience': '12+ Years Industry Experience',
            'established': 'September 2023',
            'gstin': '06BIYPK7127F1ZV',
            'udyam_number': 'UDYAM-HR-05-0093212',
            'udyam_type': 'Micro Enterprise',
            'nic_code': '28221',
            'phone_primary': '+91-9991535590',
            'phone_secondary': '+91-8930294103',
            'email': 'growtechengineers911@gmail.com',
            'location': 'Main Market, Fazalwas, Tauru Road, Pachgaon, Manesar, Gurugram, Haryana - 122413',
            'facilities_area': new_facilities,
            'manpower': '15+ Technical Experts & Toolmakers',
            'power_backup': '100% DG Genset Backup',
            'working_hours': 'Mon - Sat: 8:30 AM - 6:30 PM',
            'vision': 'To become a globally recognized tooling and machining partner.',
            'mission': 'Deliver uncompromising quality, zero defects, and on-time engineering.',
            'intro_text': 'GROWTECH ENGINEERS is an established engineering manufacturer.',
            'csrf_token': csrf
        }, follow_redirects=True)

        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Company profile and settings updated successfully', res.data)

        # Verify public page reflects the updated content
        company_res = self.client.get('/company')
        self.assertEqual(company_res.status_code, 200)
        self.assertIn(new_facilities.encode('utf-8'), company_res.data)

    # =========================================================================
    # 4. GALLERY MEDIA MANAGEMENT TESTS
    # =========================================================================

    def test_gallery_media_crud(self):
        """Test gallery photo upload, toggle status, and deletion"""
        self.login_admin()
        csrf = self.get_csrf_token()

        media_title = "CNC 5-Axis Milling Center Workstation"
        dummy_file = (io.BytesIO(b'Fake-PNG-Image-Bytes-12345'), 'cnc_machine.png')

        # 1. Add Gallery item
        add_res = self.client.post('/admin/gallery/add', data={
            'title': media_title,
            'category': 'Machinery',
            'file_type': 'image',
            'caption': 'High precision milling center for dies',
            'is_published': '1',
            'media_file': dummy_file,
            'csrf_token': csrf
        }, content_type='multipart/form-data', follow_redirects=True)

        self.assertEqual(add_res.status_code, 200)
        self.assertIn(b'added successfully', add_res.data)

        # Find gallery ID
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM gallery WHERE title = ?", (media_title,))
        item = c.fetchone()
        conn.close()

        self.assertIsNotNone(item)
        item_id = item['id']

        # 2. Toggle gallery item
        toggle_res = self.client.post(f'/admin/gallery/toggle/{item_id}', data={
            'csrf_token': csrf
        }, follow_redirects=True)
        self.assertEqual(toggle_res.status_code, 200)

        # 3. Delete gallery item
        del_res = self.client.post(f'/admin/gallery/delete/{item_id}', data={
            'csrf_token': csrf
        }, follow_redirects=True)
        self.assertEqual(del_res.status_code, 200)
        self.assertIn(b'deleted successfully', del_res.data)

    # =========================================================================
    # 5. CERTIFICATES MANAGEMENT TESTS
    # =========================================================================

    def test_certificates_crud(self):
        """Test certificate creation and deletion"""
        self.login_admin()
        csrf = self.get_csrf_token()

        cert_title = "ISO/IEC 17025 Calibration Competence Document"
        dummy_doc = (io.BytesIO(b'%PDF-1.4 Fake-PDF-Bytes'), 'calibration_cert.pdf')

        # Add certificate
        res = self.client.post('/admin/certificates/add', data={
            'title': cert_title,
            'cert_number': 'CAL-2024-9912',
            'issuing_authority': 'National Accreditation Board',
            'issue_date': '2024-03-15',
            'description': 'Calibration compliance record for measuring gauges',
            'is_published': '1',
            'cert_file': dummy_doc,
            'csrf_token': csrf
        }, content_type='multipart/form-data', follow_redirects=True)

        self.assertEqual(res.status_code, 200)
        self.assertIn(b'added successfully', res.data)

        # Verify DB
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute("SELECT id FROM certificates WHERE title = ?", (cert_title,))
        cert_row = c.fetchone()
        conn.close()

        self.assertIsNotNone(cert_row)
        cert_id = cert_row[0]

        # Delete certificate
        del_res = self.client.post(f'/admin/certificates/delete/{cert_id}', data={
            'csrf_token': csrf
        }, follow_redirects=True)
        self.assertEqual(del_res.status_code, 200)

    # =========================================================================
    # 6. NEWS AND MILESTONES MANAGEMENT TESTS
    # =========================================================================

    def test_news_crud_and_public_visibility(self):
        """Test news item creation, toggle, and public visibility"""
        self.login_admin()
        csrf = self.get_csrf_token()

        news_title = "Installation of High-Tonnage 250T Hydraulic Deep Drawing Press"
        dummy_img = (io.BytesIO(b'Fake-JPEG-News-Image'), 'news_press.jpg')

        # Add news item
        add_res = self.client.post('/admin/news/add', data={
            'title': news_title,
            'category': 'Infrastructure Expansion',
            'date_display': 'March 2024',
            'summary': 'Growtech Engineers expands heavy press forming capabilities.',
            'content': 'Commissioned new 250-ton hydraulic press to support automotive deep drawing.',
            'is_published': '1',
            'event_image': dummy_img,
            'csrf_token': csrf
        }, content_type='multipart/form-data', follow_redirects=True)

        self.assertEqual(add_res.status_code, 200)

        # Check DB
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute("SELECT id, is_published FROM news_items WHERE title = ?", (news_title,))
        row = c.fetchone()
        conn.close()

        self.assertIsNotNone(row)
        news_id, is_pub = row
        self.assertEqual(is_pub, 1)

        # Check public news page
        pub_res = self.client.get('/news')
        self.assertIn(news_title.encode('utf-8'), pub_res.data)

        # Toggle news item to unpublished
        toggle_res = self.client.post(f'/admin/news/toggle/{news_id}', data={
            'csrf_token': csrf
        }, follow_redirects=True)
        self.assertEqual(toggle_res.status_code, 200)

        # Verify not in public news page
        pub_res2 = self.client.get('/news')
        self.assertNotIn(news_title.encode('utf-8'), pub_res2.data)

        # Delete news item
        del_res = self.client.post(f'/admin/news/delete/{news_id}', data={
            'csrf_token': csrf
        }, follow_redirects=True)
        self.assertEqual(del_res.status_code, 200)

    # =========================================================================
    # 7. ENQUIRY MANAGEMENT TESTS
    # =========================================================================

    def test_enquiry_status_transitions_and_deletion(self):
        """Test viewing enquiries, updating status (New -> Contacted -> Completed), and deletion"""
        # Create a test enquiry in DB
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute('''
            INSERT INTO enquiries (name, company_name, email, phone, subject, service_category, message, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'New')
        ''', (
            'Vikramaditya Sharma',
            'Hero Motocorp Vendor Partner',
            'vikram.sharma@herovendor.co.in',
            '+91-9811223344',
            'Urgent RFQ: Automated Inspection Gauges',
            'Receiving Gauges',
            'Need 4 sets of receiving gauges for tubular chassis components.'
        ))
        enquiry_id = c.lastrowid
        conn.commit()
        conn.close()

        self.login_admin()
        csrf = self.get_csrf_token()

        # View enquiry detail
        detail_res = self.client.get(f'/admin/enquiries/{enquiry_id}')
        self.assertEqual(detail_res.status_code, 200)
        self.assertIn(b'Vikramaditya Sharma', detail_res.data)
        self.assertIn(b'Hero Motocorp Vendor Partner', detail_res.data)

        # Update status to Contacted
        status_res = self.client.post(f'/admin/enquiries/status/{enquiry_id}', data={
            'status': 'Contacted',
            'csrf_token': csrf
        }, follow_redirects=True)
        self.assertEqual(status_res.status_code, 200)

        # Verify in DB
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute("SELECT status FROM enquiries WHERE id = ?", (enquiry_id,))
        status1 = c.fetchone()[0]
        self.assertEqual(status1, 'Contacted')

        # Update status to Completed
        status_res2 = self.client.post(f'/admin/enquiries/status/{enquiry_id}', data={
            'status': 'Completed',
            'csrf_token': csrf
        }, follow_redirects=True)
        self.assertEqual(status_res2.status_code, 200)

        c.execute("SELECT status FROM enquiries WHERE id = ?", (enquiry_id,))
        status2 = c.fetchone()[0]
        self.assertEqual(status2, 'Completed')

        # Delete enquiry
        del_res = self.client.post(f'/admin/enquiries/delete/{enquiry_id}', data={
            'csrf_token': csrf
        }, follow_redirects=True)
        self.assertEqual(del_res.status_code, 200)

        c.execute("SELECT COUNT(*) FROM enquiries WHERE id = ?", (enquiry_id,))
        count = c.fetchone()[0]
        conn.close()
        self.assertEqual(count, 0, "Enquiry was not deleted from DB")

    # =========================================================================
    # 8. FILE UPLOAD SECURITY TESTS
    # =========================================================================

    def test_file_upload_security_validation(self):
        """Test file extension whitelist and rejection of executable/malicious formats"""
        # Allowed files
        self.assertTrue(allowed_file('tooling_diagram.png'))
        self.assertTrue(allowed_file('factory_floor.jpg'))
        self.assertTrue(allowed_file('component.jpeg'))
        self.assertTrue(allowed_file('cad_spec.webp'))
        self.assertTrue(allowed_file('udyam_registration.pdf'))
        self.assertTrue(allowed_file('press_operation.mp4'))

        # Strictly disallowed dangerous/executable files
        self.assertFalse(allowed_file('exploit.exe'))
        self.assertFalse(allowed_file('reverse_shell.sh'))
        self.assertFalse(allowed_file('backdoor.php'))
        self.assertFalse(allowed_file('webshell.py'))
        self.assertFalse(allowed_file('malicious.js'))
        self.assertFalse(allowed_file('payload.bat'))
        self.assertFalse(allowed_file('macro.vbs'))

if __name__ == '__main__':
    unittest.main()
