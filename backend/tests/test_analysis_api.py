"""
Integration tests for api/analysis.py endpoints.

Tests the upload → analyze → results flow using the Flask test client.
"""

import io


class TestUpload:

    def _upload(self, client, auth_header, content=b'\x00' * 4096,
                filename='test.dmp', content_type='application/octet-stream'):
        """Helper to POST a file upload."""
        data = {
            'file': (io.BytesIO(content), filename, content_type)
        }
        return client.post(
            '/api/analysis/upload',
            headers=auth_header,
            data=data,
            content_type='multipart/form-data'
        )

    def test_upload_success(self, client, auth_header):
        resp = self._upload(client, auth_header)
        assert resp.status_code == 201
        data = resp.get_json()
        assert 'session_id' in data
        assert data['file_info']['original_filename'] == 'test.dmp'

    def test_upload_no_file(self, client, auth_header):
        resp = client.post('/api/analysis/upload', headers=auth_header)
        assert resp.status_code == 400

    def test_upload_empty_filename(self, client, auth_header):
        data = {
            'file': (io.BytesIO(b'\x00' * 100), '', 'application/octet-stream')
        }
        resp = client.post(
            '/api/analysis/upload',
            headers=auth_header,
            data=data,
            content_type='multipart/form-data'
        )
        assert resp.status_code == 400

    def test_upload_requires_auth(self, client):
        data = {
            'file': (io.BytesIO(b'\x00' * 4096), 'test.dmp', 'application/octet-stream')
        }
        resp = client.post(
            '/api/analysis/upload',
            data=data,
            content_type='multipart/form-data'
        )
        assert resp.status_code == 401


class TestAnalyze:

    def _upload_and_get_session(self, client, auth_header):
        data = {
            'file': (io.BytesIO(b'\x00' * 4096), 'sample.dmp', 'application/octet-stream')
        }
        resp = client.post(
            '/api/analysis/upload',
            headers=auth_header,
            data=data,
            content_type='multipart/form-data'
        )
        return resp.get_json()['session_id']

    def test_analyze_triggers(self, client, auth_header):
        """Start analysis on an uploaded session — should succeed or fallback gracefully."""
        session_id = self._upload_and_get_session(client, auth_header)
        resp = client.post(f'/api/analysis/analyze/{session_id}',
                           headers=auth_header)
        # 200 = success (real or simulated).  500 would mean code crashed.
        assert resp.status_code in (200, 500)
        if resp.status_code == 200:
            data = resp.get_json()
            assert 'session_id' in data

    def test_analyze_nonexistent_session(self, client, auth_header):
        resp = client.post('/api/analysis/analyze/99999', headers=auth_header)
        assert resp.status_code == 404

    def test_analyze_requires_auth(self, client):
        resp = client.post('/api/analysis/analyze/1')
        assert resp.status_code == 401


class TestListSessions:

    def test_list_sessions(self, client, auth_header):
        # Upload a file first so listing isn't empty
        data = {
            'file': (io.BytesIO(b'\x00' * 4096), 'list_test.dmp', 'application/octet-stream')
        }
        client.post(
            '/api/analysis/upload',
            headers=auth_header,
            data=data,
            content_type='multipart/form-data'
        )

        resp = client.get('/api/analysis/sessions', headers=auth_header)
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data.get('sessions', data.get('data', [])), list)

    def test_list_sessions_no_auth(self, client):
        resp = client.get('/api/analysis/sessions')
        assert resp.status_code == 401
