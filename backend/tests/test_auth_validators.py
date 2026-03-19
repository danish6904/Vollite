"""
Unit tests for authentication validation helpers and security utilities.

Covers: validate_email, validate_password (from api/auth.py),
        generate_secure_filename, sanitize_filename, SecurityHeaders (from utils/security.py).
"""

import re
from api.auth import validate_email, validate_password
from utils.security import generate_secure_filename, sanitize_filename, SecurityHeaders


# ── Email Validation ──────────────────────────────────────────────────────

class TestValidateEmail:

    def test_valid_emails(self):
        assert validate_email('user@example.com')
        assert validate_email('first.last@sub.domain.org')
        assert validate_email('user+tag@gmail.com')

    def test_invalid_emails(self):
        assert not validate_email('')
        assert not validate_email('no-at-sign')
        assert not validate_email('@missing-local.com')
        assert not validate_email('user@')
        assert not validate_email('user@.com')


# ── Password Validation ──────────────────────────────────────────────────

class TestValidatePassword:

    def test_valid_password(self):
        ok, msg = validate_password('StrongP4ss')
        assert ok

    def test_too_short(self):
        ok, msg = validate_password('Aa1')
        assert not ok
        assert 'at least 8' in msg

    def test_no_uppercase(self):
        ok, msg = validate_password('lowercase1')
        assert not ok
        assert 'uppercase' in msg.lower()

    def test_no_lowercase(self):
        ok, msg = validate_password('UPPERCASE1')
        assert not ok
        assert 'lowercase' in msg.lower()

    def test_no_digit(self):
        ok, msg = validate_password('NoDigitsHere')
        assert not ok
        assert 'digit' in msg.lower()


# ── Secure Filename Generation ────────────────────────────────────────────

class TestGenerateSecureFilename:

    def test_contains_extension(self):
        name = generate_secure_filename('evidence.dmp')
        assert name.endswith('.dmp')

    def test_contains_prefix(self):
        name = generate_secure_filename('dump.mem', prefix='session_42')
        assert name.startswith('session_42_')

    def test_unique_each_call(self):
        a = generate_secure_filename('file.raw')
        b = generate_secure_filename('file.raw')
        assert a != b


# ── Filename Sanitization ────────────────────────────────────────────────

class TestSanitizeFilename:

    def test_strips_directory(self):
        assert '/' not in sanitize_filename('/etc/passwd')
        assert '\\' not in sanitize_filename('C:\\Windows\\notepad.exe')

    def test_replaces_special_chars(self):
        result = sanitize_filename('file name!@#$.dmp')
        assert re.match(r'^[\w\-_.]+$', result)

    def test_truncates_long_name(self):
        long_name = 'a' * 300 + '.dmp'
        assert len(sanitize_filename(long_name)) <= 255


# ── Security Headers ─────────────────────────────────────────────────────

class TestSecurityHeaders:

    def test_headers_added(self, app):
        """Verify all expected security headers appear on a response."""
        client = app.test_client()
        resp = client.get('/api/health')

        assert resp.headers.get('X-Content-Type-Options') == 'nosniff'
        assert resp.headers.get('X-Frame-Options') == 'DENY'
        assert resp.headers.get('X-XSS-Protection') == '1; mode=block'
        assert resp.headers.get('Referrer-Policy') == 'strict-origin-when-cross-origin'
        assert resp.headers.get('Permissions-Policy') == 'camera=(), microphone=(), geolocation=()'
        assert "default-src 'self'" in resp.headers.get('Content-Security-Policy', '')
