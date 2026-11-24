"""
GROWTECH ENGINEERS — Production Readiness & Deployment Verification Test Suite
Verifies:
1. Health check endpoint (/api/health)
2. Custom error handlers (404, 403, 500) with zero stack trace leakage
3. Persistent upload serving & path traversal protection
4. Database abstraction layer & SQL translation for PostgreSQL
5. Security headers, cookies, and upload limits
6. Backup and migration utilities
"""

import os
import io
import json
import unittest
from datetime import datetime
from app import app, UPLOAD_BASE
import db
import migrate_data

class ProductionReadinessTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()

    # =========================================================================
    # 1. HEALTH CHECK ENDPOINT TESTS
    # =========================================================================

    def test_health_check_endpoint(self):
        """Verify /api/health returns 200, valid JSON status, and no secret leakage"""
        res = self.client.get('/api/health')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.content_type, 'application/json')

        data = json.loads(res.data.decode('utf-8'))
        self.assertEqual(data.get('status'), 'healthy')
        self.assertEqual(data.get('database'), 'connected')
        self.assertIn('GROWTECH ENGINEERS', data.get('service', ''))
        self.assertIn('timestamp', data)

        # Ensure no sensitive credentials, paths, or connection strings are exposed
        raw_body = res.data.decode('utf-8')
        self.assertNotIn('password', raw_body.lower())
        self.assertNotIn('secret', raw_body.lower())
        self.assertNotIn('growtech.db', raw_body)
        self.assertNotIn('C:\\', raw_body)
        self.assertNotIn('/var/', raw_body)

    # =========================================================================
    # 2. CUSTOM ERROR HANDLING TESTS (ZERO LEAKAGE)
    # =========================================================================

    def test_custom_404_error_page(self):
        """Verify 404 returns custom industrial error page without stack traces or internal paths"""
        res = self.client.get('/invalid-page-does-not-exist-gte-404')
        self.assertEqual(res.status_code, 404)
        self.assertIn(b'404', res.data)
        self.assertIn(b'Page or Technical Asset Not Found', res.data)
        self.assertIn(b'Return to Homepage', res.data)

        # Verify no traceback / internal paths
        self.assertNotIn(b'Traceback (most recent call last)', res.data)
        self.assertNotIn(b'File "C:\\', res.data)

    def test_custom_403_forbidden_page(self):
        """Verify 403 returns custom forbidden page on CSRF failure or restricted access"""
        with self.client.session_transaction() as sess:
            sess['admin_user_id'] = 1
            sess['_csrf_token'] = 'session-csrf-secret'

        # POST without CSRF token to protected endpoint triggers abort(403)
        res = self.client.post('/admin/products/delete/999999', data={})
        self.assertEqual(res.status_code, 403)
        self.assertIn(b'403', res.data)
        self.assertIn(b'Restricted Administrator Area', res.data)
        self.assertNotIn(b'Traceback', res.data)

    # =========================================================================
    # 3. PERSISTENT UPLOADS & PATH TRAVERSAL PROTECTION
    # =========================================================================

    def test_persistent_upload_serving_and_traversal_blocking(self):
        """Verify uploaded files can be served and malicious path traversal is blocked"""
        test_dir = os.path.join(UPLOAD_BASE, 'products')
        os.makedirs(test_dir, exist_ok=True)
        test_file_path = os.path.join(test_dir, 'prod_test_safety.jpg')

        with open(test_file_path, 'wb') as f:
            f.write(b'Fake-Product-Image-Bytes-Safety')

        # 1. Normal valid access
        res = self.client.get('/static/uploads/products/prod_test_safety.jpg')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data, b'Fake-Product-Image-Bytes-Safety')

        # 2. Route alias /uploads/
        res_alias = self.client.get('/uploads/products/prod_test_safety.jpg')
        self.assertEqual(res_alias.status_code, 200)

        # 3. Path traversal attack attempt -> must be blocked with 403 or 404
        bad_paths = [
            '/static/uploads/../../app.py',
            '/uploads/../../app.py',
            '/uploads/..%2F..%2Fapp.py'
        ]
        for bad in bad_paths:
            res_bad = self.client.get(bad)
            self.assertIn(res_bad.status_code, [403, 404])
            self.assertNotIn(b'from flask import Flask', res_bad.data)

        # Cleanup
        try:
            os.remove(test_file_path)
        except OSError:
            pass

    # =========================================================================
    # 4. PRODUCTION CONFIGURATION & COOKIE SECURITY
    # =========================================================================

    def test_production_config_settings(self):
        """Verify session security, size limits, and debug flags"""
        self.assertEqual(app.config['MAX_CONTENT_LENGTH'], 16 * 1024 * 1024)
        self.assertTrue(app.config['SESSION_COOKIE_HTTPONLY'])
        self.assertEqual(app.config['SESSION_COOKIE_SAMESITE'], 'Lax')
        self.assertIsNotNone(app.config['SECRET_KEY'])

    # =========================================================================
    # 5. DATABASE ABSTRACTION & POSTGRESQL TRANSLATION
    # =========================================================================

    def test_query_translation_for_postgres(self):
        """Verify parameter placeholder ? translation to %s for PostgreSQL"""
        q1 = "SELECT * FROM users WHERE username = ? AND role = ?"
        t1 = db.translate_query(q1, to_postgres=True)
        self.assertEqual(t1, "SELECT * FROM users WHERE username = %s AND role = %s")

        # Ensure question mark inside single quotes is NOT replaced
        q2 = "SELECT * FROM company_content WHERE key_name = 'what_is_this?' AND value = ?"
        t2 = db.translate_query(q2, to_postgres=True)
        self.assertEqual(t2, "SELECT * FROM company_content WHERE key_name = 'what_is_this?' AND value = %s")

    def test_row_wrapper_access(self):
        """Verify RowWrapper supports both dict-key and index-tuple access"""
        d = {'id': 42, 'name': 'Laser Tool'}
        t = (42, 'Laser Tool')
        row = db.RowWrapper(d, t)

        self.assertEqual(row['id'], 42)
        self.assertEqual(row['name'], 'Laser Tool')
        self.assertEqual(row[0], 42)
        self.assertEqual(row[1], 'Laser Tool')
        self.assertEqual(row.get('id'), 42)
        self.assertIn('name', row)

    # =========================================================================
    # 6. BACKUP UTILITY VERIFICATION
    # =========================================================================

    def test_database_backup_utility(self):
        """Verify JSON backup creation and table integrity"""
        backup_path = migrate_data.backup_to_json()
        self.assertTrue(os.path.isfile(backup_path))

        with open(backup_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.assertIn('tables', data)
        for tbl in ['users', 'enquiries', 'products', 'company_content']:
            self.assertIn(tbl, data['tables'])

        # Cleanup test backup file
        try:
            os.remove(backup_path)
        except OSError:
            pass

if __name__ == '__main__':
    unittest.main()
