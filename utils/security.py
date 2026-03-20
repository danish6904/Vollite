import os
import secrets
import logging
from functools import wraps
from flask import request, jsonify, current_app
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from models.user import User

logger = logging.getLogger(__name__)

INSECURE_DEFAULTS = {
    'dev-secret-key-change-in-production',
    'your-secret-key-change-this-in-production',
    'your-jwt-secret-change-this-in-production',
}

def generate_secure_filename(original_filename, prefix='upload'):
    """Generate a secure filename"""
    import uuid
    from datetime import datetime
    from pathlib import Path

    # Get file extension
    file_ext = Path(original_filename).suffix.lower()

    # Generate secure filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    unique_id = str(uuid.uuid4())[:8]

    return f"{prefix}_{timestamp}_{unique_id}{file_ext}"

def sanitize_filename(filename):
    """Sanitize filename for safe storage"""
    import re

    # Remove directory path
    filename = os.path.basename(filename)

    # Replace dangerous characters
    filename = re.sub(r'[^\w\-_\.]', '_', filename)

    # Limit length
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:250] + ext

    return filename

def validate_file_size(file_size, max_size=None):
    """Validate file size"""
    if max_size is None:
        max_size = current_app.config.get('MAX_CONTENT_LENGTH', 2*1024*1024*1024)

    return file_size <= max_size

def secure_delete_file(file_path):
    """Securely delete a file"""
    try:
        if os.path.exists(file_path):
            # Overwrite with random data (simple version)
            file_size = os.path.getsize(file_path)

            with open(file_path, 'r+b') as f:
                f.write(secrets.token_bytes(file_size))
                f.flush()
                os.fsync(f.fileno())

            # Remove the file
            os.remove(file_path)
            return True
    except Exception as e:
        logger.exception("Error securely deleting file %s", file_path)
        return False

    return False

def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            verify_jwt_in_request()
            user_id = get_jwt_identity()

            # Verify user exists and is active
            user = User.query.filter_by(id=user_id, is_active=True).first()
            if not user:
                return jsonify({'error': 'Invalid or inactive user'}), 401

            return f(*args, **kwargs)
        except Exception as e:
            return jsonify({'error': 'Authentication required'}), 401

    return decorated_function

def validate_json_request(required_fields=None):
    """Decorator to validate JSON request data"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_json:
                return jsonify({'error': 'Content-Type must be application/json'}), 400

            data = request.get_json()
            if not data:
                return jsonify({'error': 'No JSON data provided'}), 400

            if required_fields:
                missing_fields = [field for field in required_fields if field not in data]
                if missing_fields:
                    return jsonify({
                        'error': 'Missing required fields',
                        'missing_fields': missing_fields
                    }), 400

            return f(*args, **kwargs)

        return decorated_function
    return decorator

class SecurityHeaders:
    """Security headers middleware"""

    @staticmethod
    def add_security_headers(response):
        """Add security headers to response"""
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "font-src 'self' data:; "
            "object-src 'none'; "
            "base-uri 'self'; "
            "frame-ancestors 'none'"
        )
        if request.is_secure:
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        return response


def validate_security_configuration(app):
    """Validate security-critical configuration for non-development environments."""
    app_env = app.config.get('APP_ENV', 'development').lower()
    if app_env in {'development', 'test', 'testing'}:
        return

    secret_key = app.config.get('SECRET_KEY', '')
    jwt_secret = app.config.get('JWT_SECRET_KEY', '')

    if not secret_key or secret_key in INSECURE_DEFAULTS or len(secret_key) < 32:
        raise RuntimeError('SECURITY: SECRET_KEY must be set to a strong value in non-development environments')

    if not jwt_secret or jwt_secret in INSECURE_DEFAULTS or len(jwt_secret) < 32:
        raise RuntimeError('SECURITY: JWT_SECRET_KEY must be set to a strong value in non-development environments')

    cors_origins = app.config.get('CORS_ORIGINS', [])
    if '*' in cors_origins:
        raise RuntimeError('SECURITY: wildcard CORS is not allowed in non-development environments')