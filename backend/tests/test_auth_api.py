"""
Integration tests for api/auth.py endpoints.

All tests use the Flask test client with an in-memory SQLite database,
so nothing touches production data.
"""

class TestRegister:

    def test_register_success(self, client):
        resp = client.post('/api/auth/register', json={
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'Secure1Pass'
        })
        assert resp.status_code == 201
        data = resp.get_json()
        assert 'access_token' in data
        assert data['user']['username'] == 'newuser'

    def test_register_missing_field(self, client):
        resp = client.post('/api/auth/register', json={
            'username': 'nomail'
        })
        assert resp.status_code == 400

    def test_register_short_username(self, client):
        resp = client.post('/api/auth/register', json={
            'username': 'ab',
            'email': 'short@example.com',
            'password': 'Secure1Pass'
        })
        assert resp.status_code == 400

    def test_register_invalid_username_chars(self, client):
        resp = client.post('/api/auth/register', json={
            'username': 'bad user!',
            'email': 'bad@example.com',
            'password': 'Secure1Pass'
        })
        assert resp.status_code == 400

    def test_register_weak_password(self, client):
        resp = client.post('/api/auth/register', json={
            'username': 'weakpw',
            'email': 'weak@example.com',
            'password': '123'
        })
        assert resp.status_code == 400

    def test_register_invalid_email(self, client):
        resp = client.post('/api/auth/register', json={
            'username': 'bademail',
            'email': 'not-an-email',
            'password': 'Secure1Pass'
        })
        assert resp.status_code == 400

    def test_register_duplicate_username(self, client, registered_user):
        resp = client.post('/api/auth/register', json={
            'username': 'testuser',
            'email': 'other@example.com',
            'password': 'Secure1Pass'
        })
        assert resp.status_code == 409

    def test_register_duplicate_email(self, client, registered_user):
        resp = client.post('/api/auth/register', json={
            'username': 'otheruser',
            'email': 'test@example.com',
            'password': 'Secure1Pass'
        })
        assert resp.status_code == 409


class TestLogin:

    def test_login_success(self, client, registered_user):
        resp = client.post('/api/auth/login', json={
            'username': 'testuser',
            'password': 'TestPass123'
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'access_token' in data

    def test_login_wrong_password(self, client, registered_user):
        resp = client.post('/api/auth/login', json={
            'username': 'testuser',
            'password': 'WrongPass1'
        })
        assert resp.status_code == 401

    def test_login_unknown_user(self, client):
        resp = client.post('/api/auth/login', json={
            'username': 'ghost',
            'password': 'Whatever1'
        })
        assert resp.status_code == 401

    def test_login_missing_fields(self, client):
        resp = client.post('/api/auth/login', json={})
        assert resp.status_code == 400

    def test_login_not_json(self, client):
        resp = client.post('/api/auth/login', data='not json')
        assert resp.status_code == 400

    def test_login_rate_limited(self, app, client, registered_user):
        app.config['AUTH_LOGIN_RATE_LIMIT'] = '2 per minute'

        payload = {
            'username': 'testuser',
            'password': 'WrongPass1'
        }
        req_opts = {'environ_overrides': {'REMOTE_ADDR': '10.0.0.99'}}

        first = client.post('/api/auth/login', json=payload, **req_opts)
        second = client.post('/api/auth/login', json=payload, **req_opts)
        third = client.post('/api/auth/login', json=payload, **req_opts)

        assert first.status_code == 401
        assert second.status_code == 401
        assert third.status_code == 429


class TestProfile:

    def test_get_profile(self, client, auth_header):
        resp = client.get('/api/auth/profile', headers=auth_header)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['user']['username'] == 'testuser'

    def test_profile_no_auth(self, client):
        resp = client.get('/api/auth/profile')
        assert resp.status_code == 401


class TestChangePassword:

    def test_change_password_success(self, client, auth_header):
        resp = client.post('/api/auth/change-password', headers=auth_header, json={
            'current_password': 'TestPass123',
            'new_password': 'NewPass456'
        })
        assert resp.status_code == 200

        # Verify new password works
        resp2 = client.post('/api/auth/login', json={
            'username': 'testuser',
            'password': 'NewPass456'
        })
        assert resp2.status_code == 200

    def test_change_password_wrong_current(self, client, auth_header):
        resp = client.post('/api/auth/change-password', headers=auth_header, json={
            'current_password': 'WrongCurrent1',
            'new_password': 'NewPass456'
        })
        assert resp.status_code == 401

    def test_change_password_weak_new(self, client, auth_header):
        resp = client.post('/api/auth/change-password', headers=auth_header, json={
            'current_password': 'TestPass123',
            'new_password': '123'
        })
        assert resp.status_code == 400


class TestVerifyToken:

    def test_valid_token(self, client, auth_header):
        resp = client.post('/api/auth/verify-token', headers=auth_header)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['valid'] is True

    def test_invalid_token(self, client):
        resp = client.post('/api/auth/verify-token',
                           headers={'Authorization': 'Bearer bad.token.here'})
        assert resp.status_code in (401, 422)
