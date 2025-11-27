"""
Tests for the Supabase REST API client.

These tests verify that the REST client provides the same interface
as the official SDK and properly constructs REST API requests.
"""
import unittest
from services.supabase_rest_client import (
    create_client,
    Client,
    SupabaseRestClient,
    QueryBuilder,
    SupabaseResponse,
)


class TestSupabaseRestClient(unittest.TestCase):
    """Tests for SupabaseRestClient."""

    def setUp(self):
        """Set up test client."""
        self.client = create_client(
            'https://example.supabase.co',
            'test-api-key'
        )

    def test_create_client(self):
        """Test that create_client returns a SupabaseRestClient."""
        self.assertIsInstance(self.client, SupabaseRestClient)

    def test_client_type_alias(self):
        """Test that Client type alias works."""
        self.assertEqual(Client, SupabaseRestClient)

    def test_client_has_storage(self):
        """Test that client has storage attribute."""
        self.assertTrue(hasattr(self.client, 'storage'))

    def test_table_returns_query_builder(self):
        """Test that table() returns a QueryBuilder."""
        qb = self.client.table('test_table')
        self.assertIsInstance(qb, QueryBuilder)


class TestQueryBuilder(unittest.TestCase):
    """Tests for QueryBuilder."""

    def setUp(self):
        """Set up test client and query builder."""
        self.client = create_client(
            'https://example.supabase.co',
            'test-api-key'
        )
        self.qb = self.client.table('employees')

    def test_select_returns_self(self):
        """Test that select() returns self for chaining."""
        result = self.qb.select('*')
        self.assertIs(result, self.qb)

    def test_eq_filter(self):
        """Test that eq() adds filter and returns self."""
        result = self.qb.eq('id', '123')
        self.assertIs(result, self.qb)
        self.assertIn('id=eq.123', self.qb._filters)

    def test_multiple_filters(self):
        """Test chaining multiple filters."""
        self.qb.eq('status', 'active').gt('age', 18).limit(10)
        self.assertIn('status=eq.active', self.qb._filters)
        self.assertIn('age=gt.18', self.qb._filters)
        self.assertEqual(self.qb._limit_value, 10)

    def test_insert_sets_method(self):
        """Test that insert() sets POST method."""
        self.qb.insert({'name': 'John'})
        self.assertEqual(self.qb._method, 'POST')

    def test_update_sets_method(self):
        """Test that update() sets PATCH method."""
        self.qb.update({'name': 'Jane'})
        self.assertEqual(self.qb._method, 'PATCH')

    def test_delete_sets_method(self):
        """Test that delete() sets DELETE method."""
        self.qb.delete()
        self.assertEqual(self.qb._method, 'DELETE')

    def test_upsert_sets_conflict(self):
        """Test that upsert() sets on_conflict."""
        self.qb.upsert({'id': 1, 'name': 'John'}, on_conflict='id')
        self.assertEqual(self.qb._upsert_conflict, 'id')

    def test_order_asc(self):
        """Test order() ascending."""
        self.qb.order('created_at', desc=False)
        self.assertEqual(self.qb._order_column, 'created_at.asc')

    def test_order_desc(self):
        """Test order() descending."""
        self.qb.order('created_at', desc=True)
        self.assertEqual(self.qb._order_column, 'created_at.desc')

    def test_limit(self):
        """Test limit()."""
        self.qb.limit(10)
        self.assertEqual(self.qb._limit_value, 10)

    def test_offset(self):
        """Test offset()."""
        self.qb.offset(20)
        self.assertEqual(self.qb._offset_value, 20)

    def test_build_url(self):
        """Test URL building."""
        self.qb.select('id, name').eq('status', 'active').limit(5)
        url = self.qb._build_url()
        self.assertIn('/rest/v1/employees', url)
        self.assertIn('select=id, name', url)
        self.assertIn('limit=5', url)

    def test_build_headers(self):
        """Test header building."""
        headers = self.qb._build_headers()
        self.assertIn('apikey', headers)
        self.assertIn('Authorization', headers)
        self.assertEqual(headers['Content-Type'], 'application/json')


class TestSupabaseResponse(unittest.TestCase):
    """Tests for SupabaseResponse."""

    def test_response_with_data(self):
        """Test response with data."""
        resp = SupabaseResponse(data=[{'id': 1}])
        self.assertEqual(resp.data, [{'id': 1}])
        self.assertIsNone(resp.error)

    def test_response_with_error(self):
        """Test response with error."""
        resp = SupabaseResponse(error={'message': 'Not found'})
        self.assertIsNone(resp.data)
        self.assertEqual(resp.error, {'message': 'Not found'})

    def test_response_bool_with_data(self):
        """Test bool conversion with data and no error."""
        resp = SupabaseResponse(data=[])
        self.assertTrue(resp)  # No error means truthy

    def test_response_bool_without_data(self):
        """Test bool conversion without data but no error."""
        resp = SupabaseResponse()
        self.assertTrue(resp)  # No error means truthy

    def test_response_bool_with_error(self):
        """Test bool conversion with error."""
        resp = SupabaseResponse(error={'message': 'Error'})
        self.assertFalse(resp)  # Error means falsy


class TestStorageClient(unittest.TestCase):
    """Tests for StorageClient."""

    def setUp(self):
        """Set up test client."""
        self.client = create_client(
            'https://example.supabase.co',
            'test-api-key'
        )

    def test_from_returns_bucket(self):
        """Test that from_() returns a StorageBucket."""
        bucket = self.client.storage.from_('test-bucket')
        self.assertTrue(hasattr(bucket, 'upload'))
        self.assertTrue(hasattr(bucket, 'remove'))
        self.assertTrue(hasattr(bucket, 'get_public_url'))

    def test_get_public_url(self):
        """Test get_public_url() returns correct URL."""
        bucket = self.client.storage.from_('my-bucket')
        url = bucket.get_public_url('path/to/file.jpg')
        expected = 'https://example.supabase.co/storage/v1/object/public/my-bucket/path/to/file.jpg'
        self.assertEqual(url, expected)


if __name__ == '__main__':
    unittest.main()
