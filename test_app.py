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

    def test_page_content_separation(self):
        """Verify each navigation page contains its own relevant content and does not duplicate other pages"""
        # 1. Homepage (/)
        home_res = self.client.get('/')
        self.assertEqual(home_res.status_code, 200)
        self.assertIn(b'hero-industrial', home_res.data)
        self.assertIn(b'At A Glance', home_res.data)
        self.assertIn(b'Manufacturing Capabilities', home_res.data)
        self.assertIn(b'Featured Products &amp; Deliverables', home_res.data)
        self.assertIn(b'Machinery &amp; Manufacturing Setup', home_res.data)
        self.assertIn(b'Why Choose GROWTECH ENGINEERS', home_res.data)
        self.assertIn(b'Valuable Customers We Support', home_res.data)
        self.assertIn(b'Ready to Discuss Your Tooling or Manufacturing Requirements?', home_res.data)
        # Verify homepage does NOT repeat full profile table or full contact RFQ form
        self.assertNotIn(b'Official Profile Summary', home_res.data)
        self.assertNotIn(b'action="/contact" method="POST"', home_res.data)
        self.assertNotIn(b'id="home_name"', home_res.data)

        # 2. Company Page (/company)
        company_res = self.client.get('/company')
        self.assertEqual(company_res.status_code, 200)
        self.assertIn(b'Official Profile Summary', company_res.data)
        self.assertIn(b'Our Vision', company_res.data)
        self.assertIn(b'Our Mission', company_res.data)
        self.assertIn(b'Factory Infrastructure &amp; Layout', company_res.data)
        self.assertIn(b'Our Machinery &amp; Equipment Setup', company_res.data)
        self.assertIn(b'The Manufacturing Team', company_res.data)
        self.assertIn(b'Government Registered Manufacturing Enterprise', company_res.data)
        self.assertIn(b'Valuable Customers We Support', company_res.data)
        # Verify company page does NOT repeat hero, full product catalog, or contact form
        self.assertNotIn(b'hero-industrial', company_res.data)
        self.assertNotIn(b'product-grid-item', company_res.data)
        self.assertNotIn(b'action="/contact" method="POST"', company_res.data)

        # 3. Products Page (/products)
        products_res = self.client.get('/products')
        self.assertEqual(products_res.status_code, 200)
        self.assertIn(b'category-filter-btn', products_res.data)
        self.assertIn(b'product-grid-item', products_res.data)
        self.assertIn(b'Have Specific Component Drawings or Part Samples?', products_res.data)
        # Verify products page does NOT repeat profile summary, vision/mission, or contact form
        self.assertNotIn(b'Official Profile Summary', products_res.data)
        self.assertNotIn(b'Our Vision', products_res.data)
        self.assertNotIn(b'action="/contact" method="POST"', products_res.data)

        # 4. News Page (/news)
        news_res = self.client.get('/news')
        self.assertEqual(news_res.status_code, 200)
        self.assertIn(b'Verified Manufacturing Milestones', news_res.data)
        self.assertIn(b'news-card', news_res.data)
        self.assertIn(b'Schedule a Plant Visit &amp; Technical Review', news_res.data)
        # Verify news page does NOT repeat product catalog or profile summary
        self.assertNotIn(b'product-grid-item', news_res.data)
        self.assertNotIn(b'Official Profile Summary', news_res.data)
        self.assertNotIn(b'action="/contact" method="POST"', news_res.data)

        # 5. Contact Page (/contact)
        contact_res = self.client.get('/contact')
        self.assertEqual(contact_res.status_code, 200)
        self.assertIn(b'gt-enquiry-form', contact_res.data)
        self.assertIn(b'action="/contact" method="POST"', contact_res.data)
        self.assertIn(b'Request Technical Quotation / Enquiry', contact_res.data)
        self.assertIn(b'contact-info-card', contact_res.data)
        self.assertIn(b'Location &amp; Connectivity in Manesar', contact_res.data)
        # Verify contact page does NOT repeat product catalog or hero
        self.assertNotIn(b'product-grid-item', contact_res.data)
        self.assertNotIn(b'hero-industrial', contact_res.data)

if __name__ == '__main__':
    unittest.main()
