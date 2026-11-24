import os
import unittest
import sqlite3
from app import app, DATABASE, GENUINE_CUSTOMERS

class GrowtechEngineersTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()

    def test_routes_status_200(self):
        """Test all public pages return status 200"""
        endpoints = ['/', '/company', '/products', '/news', '/contact']
        for endpoint in endpoints:
            response = self.client.get(endpoint)
            self.assertEqual(response.status_code, 200, f"Endpoint {endpoint} failed with code {response.status_code}")
            self.assertIn(b'GROWTECH ENGINEERS', response.data)
            self.assertIn(b'GTE', response.data)

    def test_homepage_regression_and_components(self):
        """Regression test: Homepage renders HTTP 200 without 500 error or template failures"""
        original_debug = app.config.get('DEBUG', False)
        app.config['DEBUG'] = False
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        self.assertNotIn(b'Temporary Processing Error', res.data)
        self.assertNotIn(b'500 - System Error', res.data)
        self.assertIn(b'Precision Engineering', res.data)
        self.assertIn(b'Jigs and Fixtures', res.data)
        self.assertIn(b'Receiving Gauges', res.data)
        self.assertIn(b'Pachgaon', res.data)
        self.assertIn(b'9991535590', res.data)
        app.config['DEBUG'] = original_debug

    def test_company_details_present(self):
        """Verify key required company information is rendered across pages"""
        response = self.client.get('/')
        self.assertIn(b'Naresh Kumar', response.data)
        self.assertIn(b'9991535590', response.data)
        self.assertIn(b'wa.me/919991535590', response.data)
        self.assertNotIn(b'8930294103', response.data)
        self.assertIn(b'growtechengineers911@gmail.com', response.data)
        self.assertIn(b'Pachgaon', response.data)
        self.assertIn(b'Manesar', response.data)
        self.assertIn(b'UDYAM-HR-05-0093212', response.data)
        self.assertIn(b'06BIYPK7127F1ZV', response.data)

    def test_removed_phone_and_quote_buttons(self):
        """Verify that +91-8930294103 and redundant 'Request a Quote' buttons are removed from all public pages"""
        endpoints = ['/', '/company', '/products', '/news', '/contact']
        for ep in endpoints:
            res = self.client.get(ep)
            self.assertEqual(res.status_code, 200)
            self.assertNotIn(b'8930294103', res.data, f"Endpoint {ep} still contains removed phone 8930294103")
            self.assertNotIn(b'Request a Quote', res.data, f"Endpoint {ep} still contains 'Request a Quote' button")
            self.assertNotIn(b'Request Quote', res.data, f"Endpoint {ep} still contains 'Request Quote'")
            self.assertIn(b'9991535590', res.data, f"Endpoint {ep} is missing primary phone 9991535590")

    def test_products_categories(self):
        """Check all 6 required product categories exist"""
        response = self.client.get('/products')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Jigs &amp; Fixtures', response.data)
        self.assertIn(b'Receiving Gauges', response.data)
        self.assertIn(b'Press Tools &amp; Dies', response.data)
        self.assertIn(b'Hydraulic Presses', response.data)
        self.assertIn(b'Trolleys &amp; Racks', response.data)
        self.assertIn(b'Engineering Solutions', response.data)

    def test_contact_form_submission_and_db(self):
        """Test valid form submission with subject stores data into SQLite database"""
        post_data = {
            'name': 'Senior Production Head',
            'company_name': 'Precision Auto Parts Pvt Ltd',
            'email': 'head.production@precisionautoparts.com',
            'phone': '+91-9876543210',
            'subject': 'RFQ for Progressive Hydraulic Tooling Set',
            'service_category': 'Hydraulic Presses',
            'message': 'We require a quote for progressive tooling for our 150-ton hydraulic press forming line.'
        }
        response = self.client.post('/contact', data=post_data, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Your enquiry has been received successfully', response.data)

        # Check in SQLite database
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("SELECT name, email, phone, subject, service_category FROM enquiries WHERE email = ?", ('head.production@precisionautoparts.com',))
        row = cursor.fetchone()
        conn.close()

        self.assertIsNotNone(row, "Enquiry was not saved into SQLite database")
        self.assertEqual(row[0], 'Senior Production Head')
        self.assertEqual(row[1], 'head.production@precisionautoparts.com')
        self.assertEqual(row[3], 'RFQ for Progressive Hydraulic Tooling Set')

    def test_contact_form_validation_failure(self):
        """Test that invalid form data is rejected with appropriate flash error"""
        invalid_data = {
            'name': 'A',  # too short
            'company_name': '',
            'email': 'invalid-email-address',
            'phone': '123',  # too short
            'subject': '',  # missing subject
            'service_category': 'Jigs and Fixtures',
            'message': 'short'  # less than 10 characters
        }
        response = self.client.post('/contact', data=invalid_data, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Please provide a valid business email address', response.data)

    def test_key_static_assets_resolve(self):
        """Test that logo, real factory photos, and customer logos resolve with HTTP 200"""
        assets = [
            '/static/images/logo.png',
            '/static/images/factory/main_entrance.jpg',
            '/static/images/factory/vmc_machine.jpg',
            '/static/images/factory/milling_machines.jpg',
            '/static/images/factory/inspection_room.jpg',
            '/static/images/products/jigs_fixtures_real.jpg',
            '/static/images/products/receiving_gauge_real.jpg',
            '/static/images/products/press_tool_bending.jpg',
            '/static/images/customers/toyota_boshoku.png',
            '/static/images/customers/atma.jpg',
            '/static/images/customers/nitto.jpg',
            '/static/images/certificates/udyam_badge.svg'
        ]
        for asset in assets:
            res = self.client.get(asset)
            self.assertEqual(res.status_code, 200, f"Static asset {asset} failed to resolve!")

if __name__ == '__main__':
    unittest.main()
