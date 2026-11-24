"""
GROWTECH ENGINEERS — Supabase Storage & Ephemeral Filesystem Test Suite (test_supabase_storage.py)
Tests:
1. Fallback to local storage when Supabase environment variables are unset.
2. Supabase Storage REST upload & delete via mock HTTP transport.
3. Factory static asset protection against accidental deletion.
4. Media URL resolution (static assets, local uploads, Supabase cloud URLs).
5. Ephemeral filesystem resilience (zero disk reliance on Render Free tier).
6. Admin product image lifecycle (upload -> replace -> delete) with Supabase Storage enabled.
"""

import os
import io
import json
import unittest
from unittest.mock import patch, MagicMock
import urllib.request
import urllib.error

# Import app and modules
from app import app, get_db, allowed_file, save_uploaded_file, delete_uploaded_file
import storage

class TestSupabaseStorage(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    # =========================================================================
    # 1. LOCAL STORAGE FALLBACK TESTS
    # =========================================================================

    def test_supabase_disabled_when_env_unset(self):
        """Verify that Supabase Storage is disabled when credentials are unset"""
        with patch.dict(os.environ, {}, clear=True):
            self.assertFalse(storage.is_supabase_storage_enabled())

    def test_local_upload_when_supabase_disabled(self):
        """Verify file saves to local disk when Supabase is not configured"""
        with patch.dict(os.environ, {'SUPABASE_URL': '', 'SUPABASE_KEY': ''}):
            data = io.BytesIO(b"fake image data")
            data.filename = "test_local.jpg"
            result_path = storage.save_media(data, 'products')
            self.assertIsNotNone(result_path)
            self.assertTrue(result_path.startswith('uploads/products/'))

            # Verify file exists on local disk
            local_full = os.path.join(storage.get_upload_base(), result_path.replace('uploads/', ''))
            self.assertTrue(os.path.isfile(local_full))

            # Clean up
            storage.delete_media(result_path)
            self.assertFalse(os.path.isfile(local_full))

    # =========================================================================
    # 2. MEDIA URL RESOLUTION TESTS
    # =========================================================================

    def test_resolve_media_url_scenarios(self):
        """Verify resolve_media_url handles all 4 asset source categories accurately"""
        # 1. Empty / None
        self.assertEqual(storage.resolve_media_url(None), '/static/images/logo.png')
        self.assertEqual(storage.resolve_media_url(''), '/static/images/logo.png')

        # 2. Supabase Cloud Storage public URL
        cloud_url = 'https://abcdefgh.supabase.co/storage/v1/object/public/growtech-uploads/products/test.jpg'
        self.assertEqual(storage.resolve_media_url(cloud_url), cloud_url)

        # 3. Local upload path
        self.assertEqual(storage.resolve_media_url('uploads/products/item_01.jpg'), '/static/uploads/products/item_01.jpg')
        self.assertEqual(storage.resolve_media_url('/uploads/products/item_01.jpg'), '/static/uploads/products/item_01.jpg')

        # 4. Committed factory assets in static/images
        self.assertEqual(storage.resolve_media_url('products/jigs_fixtures_real.jpg'), '/static/images/products/jigs_fixtures_real.jpg')
        self.assertEqual(storage.resolve_media_url('factory/main_entrance.jpg'), '/static/images/factory/main_entrance.jpg')
        self.assertEqual(storage.resolve_media_url('certificates/udyam_badge.svg'), '/static/images/certificates/udyam_badge.svg')

    # =========================================================================
    # 3. SUPABASE REST UPLOAD TESTS (MOCKED TEST DOUBLE)
    # =========================================================================

    @patch('urllib.request.urlopen')
    def test_upload_to_supabase_success(self, mock_urlopen):
        """Test Supabase REST upload endpoint invocation, headers, and URL generation"""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        env = {
            'SUPABASE_URL': 'https://mockproject.supabase.co',
            'SUPABASE_KEY': 'mock-service-role-key-xyz123',
            'SUPABASE_BUCKET': 'growtech-uploads'
        }
        with patch.dict(os.environ, env):
            self.assertTrue(storage.is_supabase_storage_enabled())

            test_bytes = b"sample binary image content"
            public_url = storage.upload_to_supabase(test_bytes, 'products/item123.jpg', content_type='image/jpeg')

            expected_url = 'https://mockproject.supabase.co/storage/v1/object/public/growtech-uploads/products/item123.jpg'
            self.assertEqual(public_url, expected_url)

            # Check request details
            self.assertEqual(mock_urlopen.call_count, 1)
            req = mock_urlopen.call_args[0][0]
            self.assertEqual(req.full_url, 'https://mockproject.supabase.co/storage/v1/object/growtech-uploads/products/item123.jpg')
            self.assertEqual(req.get_header('Authorization'), 'Bearer mock-service-role-key-xyz123')
            self.assertEqual(req.get_header('Apikey'), 'mock-service-role-key-xyz123')
            self.assertEqual(req.get_header('Content-type'), 'image/jpeg')
            self.assertEqual(req.get_header('X-upsert'), 'true')

    @patch('urllib.request.urlopen')
    def test_delete_from_supabase_success(self, mock_urlopen):
        """Test Supabase REST delete endpoint invocation given a full public URL"""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        env = {
            'SUPABASE_URL': 'https://mockproject.supabase.co',
            'SUPABASE_KEY': 'mock-service-role-key-xyz123',
            'SUPABASE_BUCKET': 'growtech-uploads'
        }
        with patch.dict(os.environ, env):
            target_url = 'https://mockproject.supabase.co/storage/v1/object/public/growtech-uploads/products/prod_999.jpg'
            deleted = storage.delete_from_supabase(target_url)
            self.assertTrue(deleted)

            req = mock_urlopen.call_args[0][0]
            self.assertEqual(req.full_url, 'https://mockproject.supabase.co/storage/v1/object/growtech-uploads/products/prod_999.jpg')
            self.assertEqual(req.get_method(), 'DELETE')

    # =========================================================================
    # 4. FACTORY ASSET PROTECTION TESTS
    # =========================================================================

    def test_factory_stock_photos_protected_from_deletion(self):
        """Verify factory assets committed in static/images are never deleted"""
        protected_items = [
            'factory/main_entrance.jpg',
            'factory/inner_infrastructure.jpg',
            'products/jigs_fixtures_real.jpg',
            'products/receiving_gauge_real.jpg',
            'certificates/udyam_badge.svg',
            'customers/toyota_boshoku.png'
        ]
        for asset in protected_items:
            self.assertTrue(storage.is_protected_asset(asset))
            # delete_media should return False and never attempt filesystem removal
            self.assertFalse(storage.delete_media(asset))

    # =========================================================================
    # 5. EPHEMERAL FILESYSTEM RESILIENCE
    # =========================================================================

    def test_ephemeral_filesystem_resilience(self):
        """Verify that when local container disk is wiped, Supabase URL resolves permanently"""
        # When an admin uploads with Supabase enabled, the stored URL is absolute
        cloud_url = 'https://xyzproject.supabase.co/storage/v1/object/public/growtech-uploads/products/part_101.jpg'

        # Even with local uploads directory empty/wiped:
        url_resolved = storage.resolve_media_url(cloud_url)
        self.assertEqual(url_resolved, cloud_url)
        # Verify it never refers to ephemeral container paths
        self.assertFalse(url_resolved.startswith('/static/uploads/'))

    # =========================================================================
    # 6. ADMIN PRODUCT UPLOAD LIFECYCLE WITH SUPABASE ENABLED
    # =========================================================================

    @patch('urllib.request.urlopen')
    def test_admin_product_upload_and_delete_with_supabase(self, mock_urlopen):
        """Test full admin product add, edit image replacement, and delete lifecycle"""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        env = {
            'SUPABASE_URL': 'https://mockproject.supabase.co',
            'SUPABASE_KEY': 'mock-key',
            'SUPABASE_BUCKET': 'growtech-uploads'
        }

        with patch.dict(os.environ, env):
            # 1. Login as owner
            with self.client.session_transaction() as sess:
                sess['admin_user_id'] = 1
                sess['admin_username'] = 'admin'
                sess['_csrf_token'] = 'test-token'

            # 2. Add product with image
            product_data = {
                'csrf_token': 'test-token',
                'title': 'Supabase High-Precision Jigs',
                'category': 'Jigs & Fixtures',
                'tag': 'Precision Tooling',
                'summary': 'Cloud-backed precision tooling',
                'description': 'Machined components tested with cloud storage integration.',
                'features': 'Hardened Alloy Steel\n+/- 0.005mm Tolerance',
                'applications': 'Automotive Chassis\nAssembly Quality Check',
                'status_note': 'Photographed on facility floor',
                'is_featured': '1',
                'is_published': '1',
                'primary_image': (io.BytesIO(b"image data 1"), 'fixture_01.jpg')
            }
            res = self.client.post('/admin/products/add', data=product_data, content_type='multipart/form-data', follow_redirects=True)
            self.assertEqual(res.status_code, 200)

            # Verify in DB that product has the Supabase public URL
            db = get_db()
            prod = db.execute("SELECT id, image FROM products WHERE title = 'Supabase High-Precision Jigs'").fetchone()
            self.assertIsNotNone(prod)
            prod_id = prod['id']
            first_image_url = prod['image']
            self.assertTrue(first_image_url.startswith('https://mockproject.supabase.co/storage/v1/object/public/growtech-uploads/products/'))

            # 3. Edit product and replace image
            edit_data = {
                'csrf_token': 'test-token',
                'title': 'Supabase High-Precision Jigs',
                'category': 'Jigs & Fixtures',
                'tag': 'Precision Tooling',
                'summary': 'Cloud-backed precision tooling updated',
                'description': 'Updated description.',
                'features': 'Hardened Alloy Steel',
                'applications': 'Automotive Chassis',
                'status_note': 'Updated photograph',
                'is_featured': '1',
                'is_published': '1',
                'primary_image': (io.BytesIO(b"image data 2 replacement"), 'fixture_02_new.jpg')
            }
            res_edit = self.client.post(f'/admin/products/edit/{prod_id}', data=edit_data, content_type='multipart/form-data', follow_redirects=True)
            self.assertEqual(res_edit.status_code, 200)

            # Check new image in DB
            prod_updated = db.execute("SELECT image FROM products WHERE id = ?", (prod_id,)).fetchone()
            self.assertNotEqual(prod_updated['image'], first_image_url)
            self.assertTrue(prod_updated['image'].startswith('https://mockproject.supabase.co/storage/v1/object/public/growtech-uploads/products/'))

            # 4. Delete product
            res_delete = self.client.post(f'/admin/products/delete/{prod_id}', data={'csrf_token': 'test-token'}, follow_redirects=True)
            self.assertEqual(res_delete.status_code, 200)

            # Verify product removed from DB
            prod_deleted = db.execute("SELECT id FROM products WHERE id = ?", (prod_id,)).fetchone()
            self.assertIsNone(prod_deleted)

if __name__ == '__main__':
    unittest.main()
