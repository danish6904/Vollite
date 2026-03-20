from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models import db
from models.user import User
from utils.security import validate_json_request
from utils.rate_limit import limiter
import re
import logging

auth_bp = Blueprint('auth', __name__)
logger = logging.getLogger(__name__)

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"

    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"

    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"

    if not re.search(r'\d', password):
        return False, "Password must contain at least one digit"

    return True, "Password is valid"

@auth_bp.route('/register', methods=['POST'])
@validate_json_request(['username', 'email', 'password'])
@limiter.limit(lambda: current_app.config.get('AUTH_REGISTER_RATE_LIMIT', '5 per minute'))
def register():
    """User registration endpoint"""
    try:
        data = request.get_json()

        username = data.get('username', '').strip()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')

        # Validation
        if not username or len(username) < 3:
            return jsonify({'error': 'Username must be at least 3 characters long'}), 400

        if len(username) > 50:
            return jsonify({'error': 'Username must be less than 50 characters'}), 400

        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            return jsonify({'error': 'Username can only contain letters, numbers, and underscores'}), 400

        if not validate_email(email):
            return jsonify({'error': 'Invalid email format'}), 400

        is_valid_password, password_message = validate_password(password)
        if not is_valid_password:
            return jsonify({'error': password_message}), 400

        # Check if user already exists
        existing_user = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()

        if existing_user:
            if existing_user.username == username:
                return jsonify({'error': 'Username already exists'}), 409
            else:
                return jsonify({'error': 'Email already registered'}), 409

        # Create new user
        new_user = User(username=username, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()

        # Generate access token
        access_token = create_access_token(identity=str(new_user.id))

        logger.info('auth_register_success', extra={'event': 'auth_register_success'})
        return jsonify({
            'message': 'User registered successfully',
            'access_token': access_token,
            'user': new_user.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        logger.exception('auth_register_failed', extra={'event': 'auth_register_failed'})
        return jsonify({'error': f'Registration failed: {str(e)}'}), 500

@auth_bp.route('/login', methods=['POST'])
@validate_json_request(['username', 'password'])
@limiter.limit(lambda: current_app.config.get('AUTH_LOGIN_RATE_LIMIT', '10 per minute'))
def login():
    """User login endpoint"""
    try:
        data = request.get_json()

        username = data.get('username', '').strip()
        password = data.get('password', '')

        if not username or not password:
            return jsonify({'error': 'Username and password are required'}), 400

        # Find user by username or email
        user = User.query.filter(
            (User.username == username) | (User.email == username)
        ).first()

        if not user:
            logger.warning('auth_login_invalid_user', extra={'event': 'auth_login_invalid_user'})
            return jsonify({'error': 'Invalid username or password'}), 401

        if not user.is_active:
            logger.warning('auth_login_inactive_user', extra={'event': 'auth_login_inactive_user'})
            return jsonify({'error': 'Account is disabled'}), 401

        if not user.check_password(password):
            logger.warning('auth_login_invalid_password', extra={'event': 'auth_login_invalid_password'})
            return jsonify({'error': 'Invalid username or password'}), 401

        # Generate access token
        access_token = create_access_token(identity=str(user.id))

        logger.info('auth_login_success', extra={'event': 'auth_login_success'})
        return jsonify({
            'message': 'Login successful',
            'access_token': access_token,
            'user': user.to_dict()
        }), 200

    except Exception as e:
        logger.exception('auth_login_failed', extra={'event': 'auth_login_failed'})
        return jsonify({'error': f'Login failed: {str(e)}'}), 500

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get user profile"""
    try:
        user_id = int(get_jwt_identity())
        user = User.query.filter_by(id=user_id, is_active=True).first()

        if not user:
            return jsonify({'error': 'User not found'}), 404

        return jsonify({
            'user': user.to_dict()
        }), 200

    except Exception as e:
        return jsonify({'error': f'Failed to get profile: {str(e)}'}), 500

@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
@validate_json_request(['current_password', 'new_password'])
@limiter.limit(lambda: current_app.config.get('AUTH_CHANGE_PASSWORD_RATE_LIMIT', '5 per minute'))
def change_password():
    """Change user password"""
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json()

        current_password = data.get('current_password', '')
        new_password = data.get('new_password', '')

        user = User.query.filter_by(id=user_id, is_active=True).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404

        # Verify current password
        if not user.check_password(current_password):
            return jsonify({'error': 'Current password is incorrect'}), 401

        # Validate new password
        is_valid_password, password_message = validate_password(new_password)
        if not is_valid_password:
            return jsonify({'error': password_message}), 400

        # Update password
        user.set_password(new_password)
        db.session.commit()

        return jsonify({'message': 'Password updated successfully'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to change password: {str(e)}'}), 500

@auth_bp.route('/verify-token', methods=['POST'])
@jwt_required()
@limiter.limit(lambda: current_app.config.get('AUTH_VERIFY_TOKEN_RATE_LIMIT', '30 per minute'))
def verify_token():
    """Verify if token is valid"""
    try:
        user_id = int(get_jwt_identity())
        user = User.query.filter_by(id=user_id, is_active=True).first()

        if not user:
            return jsonify({'error': 'Invalid token'}), 401

        return jsonify({
            'valid': True,
            'user': user.to_dict()
        }), 200

    except Exception as e:
        return jsonify({'error': 'Invalid token'}), 401