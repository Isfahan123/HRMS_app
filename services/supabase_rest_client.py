"""
Supabase REST API Client

A lightweight, pure-Python Supabase client that uses the REST API directly
instead of the official SDK. This allows the app to run on cPanel/shared
hosting environments that don't have Rust (required by the SDK).

This module provides a drop-in replacement for the official supabase-py library,
implementing the same interface for database and storage operations.
"""

import os
import json
import mimetypes
from typing import Dict, List, Optional, Any, Union
from urllib.parse import urlencode, quote
import requests


class SupabaseResponse:
    """Response object that mimics the Supabase SDK response structure."""
    
    def __init__(self, data: Any = None, error: Optional[Dict] = None, count: Optional[int] = None):
        self.data = data
        self.error = error
        self.count = count
    
    def __bool__(self):
        # Response is truthy when there's no error
        return self.error is None


class QueryBuilder:
    """
    Query builder that provides a fluent interface for building REST API requests.
    Mimics the Supabase SDK's query builder pattern.
    """
    
    def __init__(self, client: 'SupabaseRestClient', table_name: str):
        self._client = client
        self._table_name = table_name
        self._method = 'GET'
        self._select_columns = '*'
        self._filters: List[str] = []
        self._order_column: Optional[str] = None
        self._order_desc: bool = False
        self._limit_value: Optional[int] = None
        self._offset_value: Optional[int] = None
        self._body: Optional[Dict] = None
        self._upsert_conflict: Optional[str] = None
        self._prefer_headers: List[str] = []
        self._range_start: Optional[int] = None
        self._range_end: Optional[int] = None
        self._count_option: Optional[str] = None  # 'exact', 'planned', 'estimated'
    
    def select(self, columns: str = '*', count: Optional[str] = None) -> 'QueryBuilder':
        """
        Set columns to select.
        
        Args:
            columns: Comma-separated column names or '*' for all columns
            count: Count option - 'exact', 'planned', or 'estimated'. 
                   When provided, the response will include a count of matching rows.
        
        Returns:
            QueryBuilder for method chaining
        """
        self._select_columns = columns
        self._method = 'GET'
        if count in ('exact', 'planned', 'estimated'):
            self._count_option = count
        return self
    
    def insert(self, data: Union[Dict, List[Dict]]) -> 'QueryBuilder':
        """Insert one or more records."""
        self._method = 'POST'
        self._body = data
        self._prefer_headers.append('return=representation')
        return self
    
    def update(self, data: Dict) -> 'QueryBuilder':
        """Update records matching filters."""
        self._method = 'PATCH'
        self._body = data
        self._prefer_headers.append('return=representation')
        return self
    
    def upsert(self, data: Union[Dict, List[Dict]], on_conflict: Optional[str] = None) -> 'QueryBuilder':
        """Insert or update records based on conflict columns."""
        self._method = 'POST'
        self._body = data
        self._upsert_conflict = on_conflict
        self._prefer_headers.append('return=representation')
        self._prefer_headers.append('resolution=merge-duplicates')
        return self
    
    def delete(self) -> 'QueryBuilder':
        """Delete records matching filters."""
        self._method = 'DELETE'
        self._prefer_headers.append('return=representation')
        return self
    
    # Filter methods
    def eq(self, column: str, value: Any) -> 'QueryBuilder':
        """Filter where column equals value."""
        self._filters.append(f"{column}=eq.{self._encode_value(value)}")
        return self
    
    def neq(self, column: str, value: Any) -> 'QueryBuilder':
        """Filter where column does not equal value."""
        self._filters.append(f"{column}=neq.{self._encode_value(value)}")
        return self
    
    def gt(self, column: str, value: Any) -> 'QueryBuilder':
        """Filter where column is greater than value."""
        self._filters.append(f"{column}=gt.{self._encode_value(value)}")
        return self
    
    def gte(self, column: str, value: Any) -> 'QueryBuilder':
        """Filter where column is greater than or equal to value."""
        self._filters.append(f"{column}=gte.{self._encode_value(value)}")
        return self
    
    def lt(self, column: str, value: Any) -> 'QueryBuilder':
        """Filter where column is less than value."""
        self._filters.append(f"{column}=lt.{self._encode_value(value)}")
        return self
    
    def lte(self, column: str, value: Any) -> 'QueryBuilder':
        """Filter where column is less than or equal to value."""
        self._filters.append(f"{column}=lte.{self._encode_value(value)}")
        return self
    
    def like(self, column: str, pattern: str) -> 'QueryBuilder':
        """Filter where column matches pattern (case-sensitive)."""
        self._filters.append(f"{column}=like.{self._encode_value(pattern)}")
        return self
    
    def ilike(self, column: str, pattern: str) -> 'QueryBuilder':
        """Filter where column matches pattern (case-insensitive)."""
        self._filters.append(f"{column}=ilike.{self._encode_value(pattern)}")
        return self
    
    def is_(self, column: str, value: Any) -> 'QueryBuilder':
        """Filter where column is null or true/false."""
        self._filters.append(f"{column}=is.{str(value).lower()}")
        return self
    
    def in_(self, column: str, values: List[Any]) -> 'QueryBuilder':
        """Filter where column is in a list of values."""
        encoded = ','.join(str(v) for v in values)
        self._filters.append(f"{column}=in.({encoded})")
        return self
    
    def contains(self, column: str, value: Any) -> 'QueryBuilder':
        """Filter where column contains value (for arrays/JSON)."""
        if isinstance(value, (list, dict)):
            self._filters.append(f"{column}=cs.{json.dumps(value)}")
        else:
            self._filters.append(f"{column}=cs.{{{value}}}")
        return self
    
    def overlaps(self, column: str, value: List[Any]) -> 'QueryBuilder':
        """Filter where array column overlaps with value."""
        encoded = ','.join(str(v) for v in value)
        self._filters.append(f"{column}=ov.{{{encoded}}}")
        return self
    
    def or_(self, filters: str) -> 'QueryBuilder':
        """Apply OR filter."""
        self._filters.append(f"or=({filters})")
        return self
    
    def not_(self, column: str, operator: str, value: Any) -> 'QueryBuilder':
        """Apply NOT filter."""
        self._filters.append(f"{column}=not.{operator}.{self._encode_value(value)}")
        return self
    
    def filter(self, column: str, operator: str, value: Any) -> 'QueryBuilder':
        """
        Apply a filter using any PostgREST operator.
        
        Args:
            column: Column name to filter on
            operator: PostgREST operator (e.g., 'eq', 'neq', 'gt', 'gte', 'lt', 'lte', 'like', 'ilike', 'is', 'in', 'cs', 'cd', 'ov')
            value: Value to filter by
        
        Returns:
            QueryBuilder for method chaining
        """
        # Handle special value types
        if operator == 'in' and isinstance(value, (list, tuple)):
            # Properly encode each value in the list to prevent injection
            encoded = ','.join(self._encode_value(v) for v in value)
            self._filters.append(f"{column}=in.({encoded})")
        elif operator == 'is':
            # Validate 'is' operator values - only null, true, false are allowed
            if value is None:
                encoded_val = 'null'
            elif isinstance(value, bool):
                encoded_val = 'true' if value else 'false'
            elif isinstance(value, str) and value.lower() in ('null', 'true', 'false'):
                encoded_val = value.lower()
            else:
                # For safety, treat unknown values as null
                encoded_val = 'null'
            self._filters.append(f"{column}=is.{encoded_val}")
        else:
            self._filters.append(f"{column}={operator}.{self._encode_value(value)}")
        return self
    
    def match(self, query: Dict[str, Any]) -> 'QueryBuilder':
        """
        Match multiple columns with equality.
        
        This is a convenience method for filtering by multiple column values at once.
        
        Args:
            query: Dictionary of column-value pairs to match
        
        Returns:
            QueryBuilder for method chaining
        
        Example:
            client.table('users').match({'status': 'active', 'role': 'admin'}).execute()
        """
        for column, value in query.items():
            self.eq(column, value)
        return self
    
    # Ordering and pagination
    def order(self, column: str, desc: bool = False, nullsfirst: bool = False, nullslast: bool = False) -> 'QueryBuilder':
        """
        Order results by column.
        
        Args:
            column: Column name to order by
            desc: If True, order descending; otherwise ascending
            nullsfirst: If True, put NULL values first
            nullslast: If True, put NULL values last (takes precedence over nullsfirst if both are True)
        
        Returns:
            QueryBuilder for method chaining
        """
        direction = 'desc' if desc else 'asc'
        if nullslast:
            nulls = '.nullslast'
        elif nullsfirst:
            nulls = '.nullsfirst'
        else:
            nulls = ''
        self._order_column = f"{column}.{direction}{nulls}"
        return self
    
    def limit(self, count: int) -> 'QueryBuilder':
        """Limit the number of results."""
        self._limit_value = count
        return self
    
    def offset(self, count: int) -> 'QueryBuilder':
        """Offset the results."""
        self._offset_value = count
        return self
    
    def range(self, start: int, end: int) -> 'QueryBuilder':
        """Set range of results to return."""
        self._range_start = start
        self._range_end = end
        return self
    
    def single(self) -> 'QueryBuilder':
        """Expect a single result."""
        self._limit_value = 1
        self._prefer_headers.append('return=representation')
        return self
    
    def maybe_single(self) -> 'QueryBuilder':
        """Expect at most one result."""
        self._limit_value = 1
        return self
    
    @staticmethod
    def _encode_value(value: Any) -> str:
        """Encode value for use in URL parameters."""
        if value is None:
            return 'null'
        if isinstance(value, bool):
            return str(value).lower()
        if isinstance(value, str):
            # Quote special characters but not the entire string
            return quote(value, safe='')
        return str(value)
    
    def _build_url(self) -> str:
        """Build the complete URL for the request."""
        base_url = f"{self._client.url}/rest/v1/{self._table_name}"
        params = []
        
        if self._method == 'GET' and self._select_columns:
            params.append(f"select={self._select_columns}")
        
        params.extend(self._filters)
        
        if self._order_column:
            params.append(f"order={self._order_column}")
        
        if self._limit_value is not None:
            params.append(f"limit={self._limit_value}")
        
        if self._offset_value is not None:
            params.append(f"offset={self._offset_value}")
        
        if params:
            return f"{base_url}?{'&'.join(params)}"
        return base_url
    
    def _build_headers(self) -> Dict[str, str]:
        """Build headers for the request."""
        headers = self._client._get_headers()
        
        # Collect all Prefer header values
        prefer_values = list(self._prefer_headers)
        
        # Add count option if specified
        if self._count_option:
            prefer_values.append(f'count={self._count_option}')
        
        if self._upsert_conflict:
            prefer_values.append(f'on_conflict={self._upsert_conflict}')
        
        if prefer_values:
            headers['Prefer'] = ', '.join(prefer_values)
        
        if self._range_start is not None and self._range_end is not None:
            headers['Range'] = f'{self._range_start}-{self._range_end}'
        
        return headers
    
    def execute(self) -> SupabaseResponse:
        """Execute the query and return the response."""
        url = self._build_url()
        headers = self._build_headers()
        
        try:
            if self._method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif self._method == 'POST':
                response = requests.post(url, headers=headers, json=self._body, timeout=30)
            elif self._method == 'PATCH':
                response = requests.patch(url, headers=headers, json=self._body, timeout=30)
            elif self._method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=30)
            else:
                return SupabaseResponse(error={'message': f'Unknown method: {self._method}'})
            
            # Check for HTTP errors
            if response.status_code >= 400:
                error_data = None
                try:
                    error_data = response.json()
                except Exception:
                    error_data = {'message': response.text}
                
                # Raise an exception for error responses to match SDK behavior
                error_msg = error_data.get('message', '') if isinstance(error_data, dict) else str(error_data)
                code = error_data.get('code', '') if isinstance(error_data, dict) else ''
                raise Exception(f"PostgREST error ({response.status_code}): {code} - {error_msg}")
            
            # Parse response
            try:
                data = response.json() if response.text else []
            except json.JSONDecodeError:
                data = []
            
            # Get count from headers if available
            count = None
            content_range = response.headers.get('Content-Range')
            if content_range:
                try:
                    count = int(content_range.split('/')[-1])
                except (ValueError, IndexError):
                    pass
            
            return SupabaseResponse(data=data, count=count)
            
        except requests.RequestException as e:
            raise Exception(f"Request failed: {str(e)}")


class StorageBucket:
    """Storage bucket operations for file uploads and management."""
    
    def __init__(self, client: 'SupabaseRestClient', bucket_name: str):
        self._client = client
        self._bucket_name = bucket_name
    
    def upload(self, path: str, file: Any, file_options: Optional[Dict] = None) -> Any:
        """
        Upload a file to the storage bucket.
        
        Args:
            path: Path in the bucket where file will be stored
            file: File object (file-like object with read method)
            file_options: Optional dict with 'content-type' and other options
        
        Returns:
            Response object with 'path' attribute on success
        """
        url = f"{self._client.url}/storage/v1/object/{self._bucket_name}/{path}"
        
        headers = {
            'apikey': self._client.key,
            'Authorization': f'Bearer {self._client.key}',
        }
        
        # Determine content type
        content_type = 'application/octet-stream'
        if file_options and 'content-type' in file_options:
            content_type = file_options['content-type']
        else:
            # Try to guess from path
            guessed_type, _ = mimetypes.guess_type(path)
            if guessed_type:
                content_type = guessed_type
        
        headers['Content-Type'] = content_type
        
        # Read file content
        if hasattr(file, 'read'):
            file_content = file.read()
        else:
            file_content = file
        
        try:
            response = requests.post(url, headers=headers, data=file_content, timeout=60)
            
            if response.status_code >= 400:
                error_msg = response.text
                try:
                    error_data = response.json()
                    error_msg = error_data.get('message', error_msg)
                except Exception:
                    pass
                raise Exception(f"Storage upload failed: {error_msg}")
            
            # Create response object with path attribute
            class UploadResponse:
                def __init__(self, path: str):
                    self.path = path
            
            return UploadResponse(path)
            
        except requests.RequestException as e:
            raise Exception(f"Storage upload request failed: {str(e)}")
    
    def remove(self, paths: List[str]) -> Dict:
        """
        Remove files from the storage bucket.
        
        Args:
            paths: List of file paths to remove
        
        Returns:
            Response dict
        """
        url = f"{self._client.url}/storage/v1/object/{self._bucket_name}"
        
        headers = {
            'apikey': self._client.key,
            'Authorization': f'Bearer {self._client.key}',
            'Content-Type': 'application/json',
        }
        
        try:
            response = requests.delete(url, headers=headers, json={'prefixes': paths}, timeout=30)
            
            if response.status_code >= 400 and response.status_code != 404:
                # 404 is acceptable when file doesn't exist
                error_msg = response.text
                try:
                    error_data = response.json()
                    error_msg = error_data.get('message', error_msg)
                except Exception:
                    pass
                raise Exception(f"Storage remove failed: {error_msg}")
            
            try:
                return response.json() if response.text else {}
            except json.JSONDecodeError:
                return {}
                
        except requests.RequestException as e:
            raise Exception(f"Storage remove request failed: {str(e)}")
    
    def get_public_url(self, path: str) -> str:
        """
        Get the public URL for a file in the storage bucket.
        
        Args:
            path: Path to the file in the bucket
        
        Returns:
            Public URL string
        """
        return f"{self._client.url}/storage/v1/object/public/{self._bucket_name}/{path}"
    
    def download(self, path: str) -> bytes:
        """
        Download a file from the storage bucket.
        
        Args:
            path: Path to the file in the bucket
        
        Returns:
            File content as bytes
        """
        url = f"{self._client.url}/storage/v1/object/{self._bucket_name}/{path}"
        
        headers = {
            'apikey': self._client.key,
            'Authorization': f'Bearer {self._client.key}',
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=60)
            
            if response.status_code >= 400:
                error_msg = response.text
                try:
                    error_data = response.json()
                    error_msg = error_data.get('message', error_msg)
                except Exception:
                    pass
                raise Exception(f"Storage download failed: {error_msg}")
            
            return response.content
            
        except requests.RequestException as e:
            raise Exception(f"Storage download request failed: {str(e)}")
    
    @staticmethod
    def _sanitize_path(path: str) -> str:
        """
        Sanitize a storage path to prevent path traversal attacks.
        
        Args:
            path: Path string to sanitize
        
        Returns:
            Sanitized path string
        
        Raises:
            ValueError: If path contains dangerous components
        """
        if not path:
            return ''
        
        # Normalize path separators
        normalized = path.replace('\\', '/')
        
        # Check for path traversal attempts
        if '..' in normalized:
            raise ValueError("Path cannot contain '..'")
        
        # Remove leading slashes to prevent absolute path access
        normalized = normalized.lstrip('/')
        
        # Check for null bytes
        if '\x00' in normalized:
            raise ValueError("Path cannot contain null bytes")
        
        return normalized
    
    def list(self, path: str = '', limit: int = 100, offset: int = 0, 
             sort_by: Optional[Dict[str, str]] = None, search: Optional[str] = None) -> List[Dict]:
        """
        List files in a storage bucket directory.
        
        Args:
            path: Path prefix to list files from (empty string for root)
            limit: Maximum number of files to return (default 100)
            offset: Offset for pagination (default 0)
            sort_by: Optional sort configuration, e.g., {'column': 'name', 'order': 'asc'}
            search: Optional search term to filter file names
        
        Returns:
            List of file/folder metadata dictionaries
        
        Example:
            files = client.storage.from_('bucket').list('folder/', limit=50)
        """
        # Sanitize the path to prevent path traversal
        safe_path = self._sanitize_path(path)
        
        url = f"{self._client.url}/storage/v1/object/list/{self._bucket_name}"
        
        headers = {
            'apikey': self._client.key,
            'Authorization': f'Bearer {self._client.key}',
            'Content-Type': 'application/json',
        }
        
        body: Dict[str, Any] = {
            'prefix': safe_path,
            'limit': limit,
            'offset': offset,
        }
        
        if sort_by:
            body['sortBy'] = sort_by
        
        if search:
            body['search'] = search
        
        try:
            response = requests.post(url, headers=headers, json=body, timeout=30)
            
            if response.status_code >= 400:
                error_msg = response.text
                try:
                    error_data = response.json()
                    error_msg = error_data.get('message', error_msg)
                except Exception:
                    pass
                raise Exception(f"Storage list failed: {error_msg}")
            
            try:
                return response.json() if response.text else []
            except json.JSONDecodeError:
                return []
            
        except requests.RequestException as e:
            raise Exception(f"Storage list request failed: {str(e)}")
    
    def move(self, from_path: str, to_path: str) -> Dict:
        """
        Move a file within the storage bucket.
        
        Args:
            from_path: Current path of the file
            to_path: New path for the file
        
        Returns:
            Response dictionary with move result
        """
        # Sanitize paths to prevent path traversal
        safe_from = self._sanitize_path(from_path)
        safe_to = self._sanitize_path(to_path)
        
        url = f"{self._client.url}/storage/v1/object/move"
        
        headers = {
            'apikey': self._client.key,
            'Authorization': f'Bearer {self._client.key}',
            'Content-Type': 'application/json',
        }
        
        body = {
            'bucketId': self._bucket_name,
            'sourceKey': safe_from,
            'destinationKey': safe_to,
        }
        
        try:
            response = requests.post(url, headers=headers, json=body, timeout=30)
            
            if response.status_code >= 400:
                error_msg = response.text
                try:
                    error_data = response.json()
                    error_msg = error_data.get('message', error_msg)
                except Exception:
                    pass
                raise Exception(f"Storage move failed: {error_msg}")
            
            try:
                return response.json() if response.text else {}
            except json.JSONDecodeError:
                return {}
            
        except requests.RequestException as e:
            raise Exception(f"Storage move request failed: {str(e)}")
    
    def copy(self, from_path: str, to_path: str) -> Dict:
        """
        Copy a file within the storage bucket.
        
        Args:
            from_path: Source path of the file
            to_path: Destination path for the copy
        
        Returns:
            Response dictionary with copy result
        """
        # Sanitize paths to prevent path traversal
        safe_from = self._sanitize_path(from_path)
        safe_to = self._sanitize_path(to_path)
        
        url = f"{self._client.url}/storage/v1/object/copy"
        
        headers = {
            'apikey': self._client.key,
            'Authorization': f'Bearer {self._client.key}',
            'Content-Type': 'application/json',
        }
        
        body = {
            'bucketId': self._bucket_name,
            'sourceKey': safe_from,
            'destinationKey': safe_to,
        }
        
        try:
            response = requests.post(url, headers=headers, json=body, timeout=30)
            
            if response.status_code >= 400:
                error_msg = response.text
                try:
                    error_data = response.json()
                    error_msg = error_data.get('message', error_msg)
                except Exception:
                    pass
                raise Exception(f"Storage copy failed: {error_msg}")
            
            try:
                return response.json() if response.text else {}
            except json.JSONDecodeError:
                return {}
            
        except requests.RequestException as e:
            raise Exception(f"Storage copy request failed: {str(e)}")
    
    def create_signed_url(self, path: str, expires_in: int = 3600) -> str:
        """
        Create a signed URL for temporary access to a private file.
        
        Args:
            path: Path to the file in the bucket
            expires_in: Number of seconds until the URL expires (default 3600 = 1 hour)
        
        Returns:
            Signed URL string
        """
        # Sanitize the path to prevent path traversal
        safe_path = self._sanitize_path(path)
        
        url = f"{self._client.url}/storage/v1/object/sign/{self._bucket_name}/{safe_path}"
        
        headers = {
            'apikey': self._client.key,
            'Authorization': f'Bearer {self._client.key}',
            'Content-Type': 'application/json',
        }
        
        body = {
            'expiresIn': expires_in,
        }
        
        try:
            response = requests.post(url, headers=headers, json=body, timeout=30)
            
            if response.status_code >= 400:
                error_msg = response.text
                try:
                    error_data = response.json()
                    error_msg = error_data.get('message', error_msg)
                except Exception:
                    pass
                raise Exception(f"Storage create_signed_url failed: {error_msg}")
            
            try:
                data = response.json() if response.text else {}
                signed_url = data.get('signedURL', '')
                if signed_url and not signed_url.startswith('http'):
                    # Validate that the signed URL is a proper relative path
                    # It should start with /storage/ for Supabase signed URLs
                    if signed_url.startswith('/storage/') or signed_url.startswith('/object/'):
                        signed_url = f"{self._client.url}{signed_url}"
                    else:
                        # Invalid signed URL format - return empty
                        return ''
                return signed_url
            except json.JSONDecodeError:
                return ''
            
        except requests.RequestException as e:
            raise Exception(f"Storage create_signed_url request failed: {str(e)}")


class StorageClient:
    """Storage client that provides access to storage buckets."""
    
    def __init__(self, client: 'SupabaseRestClient'):
        self._client = client
        self._buckets: Dict[str, StorageBucket] = {}
    
    def from_(self, bucket_name: str) -> StorageBucket:
        """
        Get a storage bucket by name.
        
        Args:
            bucket_name: Name of the storage bucket
        
        Returns:
            StorageBucket instance
        """
        if bucket_name not in self._buckets:
            self._buckets[bucket_name] = StorageBucket(self._client, bucket_name)
        return self._buckets[bucket_name]


class SupabaseRestClient:
    """
    A lightweight Supabase client that uses REST API directly.
    
    This provides a drop-in replacement for the official supabase-py library,
    allowing the app to run on cPanel/shared hosting without Rust dependencies.
    
    Example usage:
        from services.supabase_rest_client import create_client
        
        client = create_client(url, key)
        
        # Select
        result = client.table('employees').select('*').eq('id', '123').execute()
        
        # Insert
        result = client.table('employees').insert({'name': 'John'}).execute()
        
        # Update
        result = client.table('employees').update({'name': 'Jane'}).eq('id', '123').execute()
        
        # Delete
        result = client.table('employees').delete().eq('id', '123').execute()
        
        # Storage
        client.storage.from_('bucket').upload('path/file.jpg', file_obj)
        url = client.storage.from_('bucket').get_public_url('path/file.jpg')
    """
    
    def __init__(self, url: str, key: str):
        """
        Initialize the Supabase REST client.
        
        Args:
            url: Supabase project URL (e.g., https://xxx.supabase.co)
            key: Supabase anon or service role key
        """
        self.url = url.rstrip('/')
        self.key = key
        self.storage = StorageClient(self)
    
    def _get_headers(self) -> Dict[str, str]:
        """Get the default headers for API requests."""
        return {
            'apikey': self.key,
            'Authorization': f'Bearer {self.key}',
            'Content-Type': 'application/json',
        }
    
    def table(self, table_name: str) -> QueryBuilder:
        """
        Get a query builder for the specified table.
        
        Args:
            table_name: Name of the database table
        
        Returns:
            QueryBuilder instance
        """
        return QueryBuilder(self, table_name)
    
    def rpc(self, function_name: str, params: Optional[Dict] = None) -> SupabaseResponse:
        """
        Call a Postgres function (RPC).
        
        Args:
            function_name: Name of the Postgres function to call
            params: Optional dictionary of parameters to pass to the function
        
        Returns:
            SupabaseResponse with the function result
        
        Example:
            result = client.rpc('get_user_count', {'department': 'engineering'})
        """
        url = f"{self.url}/rest/v1/rpc/{function_name}"
        headers = self._get_headers()
        
        try:
            if params:
                response = requests.post(url, headers=headers, json=params, timeout=30)
            else:
                response = requests.post(url, headers=headers, json={}, timeout=30)
            
            if response.status_code >= 400:
                error_data = None
                try:
                    error_data = response.json()
                except Exception:
                    error_data = {'message': response.text}
                
                error_msg = error_data.get('message', '') if isinstance(error_data, dict) else str(error_data)
                code = error_data.get('code', '') if isinstance(error_data, dict) else ''
                raise Exception(f"RPC error ({response.status_code}): {code} - {error_msg}")
            
            try:
                data = response.json() if response.text else None
            except json.JSONDecodeError:
                data = None
            
            return SupabaseResponse(data=data)
            
        except requests.RequestException as e:
            raise Exception(f"RPC request failed: {str(e)}")


# Type alias for compatibility with code that imports Client type
Client = SupabaseRestClient


def create_client(url: str, key: str) -> SupabaseRestClient:
    """
    Create a Supabase REST client.
    
    This is a drop-in replacement for supabase.create_client().
    
    Args:
        url: Supabase project URL
        key: Supabase API key
    
    Returns:
        SupabaseRestClient instance
    """
    return SupabaseRestClient(url, key)
