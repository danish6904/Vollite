# Create the API endpoints - Phase 1

phase1_api = {
    "api/__init__.py": """# API package initialization
from flask import Blueprint

def register_blueprints(app):
    \"\"\"Register all API blueprints\"\"\"
    from .auth import auth_bp
    from .analysis import analysis_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(analysis_bp, url_prefix='/api/analysis')
""",

    "api/auth.py": """from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import check_password_hash
from models import db
from models.user import User
from utils.security import validate_json_request
import re

auth_bp = Blueprint('auth', __name__)

def validate_email(email):
    \"\"\"Validate email format\"\"\"
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    \"\"\"Validate password strength\"\"\"
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r'\\d', password):
        return False, "Password must contain at least one digit"
    
    return True, "Password is valid"

@auth_bp.route('/register', methods=['POST'])
@validate_json_request(['username', 'email', 'password'])
def register():
    \"\"\"User registration endpoint\"\"\"
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
        access_token = create_access_token(identity=new_user.id)
        
        return jsonify({
            'message': 'User registered successfully',
            'access_token': access_token,
            'user': new_user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Registration failed: {str(e)}'}), 500

@auth_bp.route('/login', methods=['POST'])
@validate_json_request(['username', 'password'])
def login():
    \"\"\"User login endpoint\"\"\"
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
            return jsonify({'error': 'Invalid username or password'}), 401
        
        if not user.is_active:
            return jsonify({'error': 'Account is disabled'}), 401
        
        if not user.check_password(password):
            return jsonify({'error': 'Invalid username or password'}), 401
        
        # Generate access token
        access_token = create_access_token(identity=user.id)
        
        return jsonify({
            'message': 'Login successful',
            'access_token': access_token,
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Login failed: {str(e)}'}), 500

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    \"\"\"Get user profile\"\"\"
    try:
        user_id = get_jwt_identity()
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
def change_password():
    \"\"\"Change user password\"\"\"
    try:
        user_id = get_jwt_identity()
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
def verify_token():
    \"\"\"Verify if token is valid\"\"\"
    try:
        user_id = get_jwt_identity()
        user = User.query.filter_by(id=user_id, is_active=True).first()
        
        if not user:
            return jsonify({'error': 'Invalid token'}), 401
        
        return jsonify({
            'valid': True,
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Invalid token'}), 401""",

    "api/analysis.py": """from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
import os
import uuid
from datetime import datetime

from models import db
from models.user import User
from models.analysis import AnalysisSession, AnalysisResult, Alert
from services.file_validator import FileValidator
from services.volatility_service import VolatilityService
from utils.security import generate_secure_filename, secure_delete_file

analysis_bp = Blueprint('analysis', __name__)

def get_current_user():
    \"\"\"Get current authenticated user\"\"\"
    user_id = get_jwt_identity()
    return User.query.filter_by(id=user_id, is_active=True).first()

@analysis_bp.route('/upload', methods=['POST'])
@jwt_required()
def upload_file():
    \"\"\"Upload memory dump file\"\"\"
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Check if file is in request
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Generate secure filename
        original_filename = file.filename
        session_id = str(uuid.uuid4())
        secure_name = generate_secure_filename(original_filename, f'session_{session_id}')
        
        # Save file temporarily for validation
        upload_folder = current_app.config['UPLOAD_FOLDER']
        os.makedirs(upload_folder, exist_ok=True)
        file_path = os.path.join(upload_folder, secure_name)
        
        file.save(file_path)
        
        # Validate file
        validator = FileValidator()
        validation_result = validator.validate_file(file, file_path)
        
        if not validation_result['valid']:
            # Remove invalid file
            secure_delete_file(file_path)
            return jsonify({
                'error': 'File validation failed',
                'details': validation_result['errors']
            }), 400
        
        # Create analysis session
        session = AnalysisSession(
            user_id=user.id,
            filename=secure_name,
            original_filename=original_filename,
            file_hash=validation_result['file_info']['sha256'],
            file_size=validation_result['file_info']['file_size'],
            mime_type=validation_result['file_info'].get('mime_type')
        )
        
        db.session.add(session)
        db.session.commit()
        
        response_data = {
            'message': 'File uploaded successfully',
            'session_id': session.id,
            'file_info': {
                'original_filename': original_filename,
                'file_size': validation_result['file_info']['file_size'],
                'file_hash': validation_result['file_info']['sha256'],
                'mime_type': validation_result['file_info'].get('mime_type')
            }
        }
        
        # Include warnings if any
        if validation_result['warnings']:
            response_data['warnings'] = validation_result['warnings']
        
        return jsonify(response_data), 201
        
    except Exception as e:
        # Clean up file if session creation failed
        if 'file_path' in locals() and os.path.exists(file_path):
            secure_delete_file(file_path)
        
        db.session.rollback()
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

@analysis_bp.route('/analyze/<int:session_id>', methods=['POST'])
@jwt_required()
def start_analysis(session_id):
    \"\"\"Start memory dump analysis\"\"\"
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get analysis session
        session = AnalysisSession.query.filter_by(
            id=session_id,
            user_id=user.id
        ).first()
        
        if not session:
            return jsonify({'error': 'Analysis session not found'}), 404
        
        if session.analysis_status not in ['uploaded', 'failed']:
            return jsonify({'error': f'Cannot start analysis. Current status: {session.analysis_status}'}), 400
        
        # Update status to analyzing
        session.update_status('analyzing')
        
        # Get file path
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], session.filename)
        
        if not os.path.exists(file_path):
            session.update_status('failed', 'Memory dump file not found')
            return jsonify({'error': 'Memory dump file not found'}), 404
        
        # Initialize Volatility service
        vol_service = VolatilityService()
        
        # Check if Volatility is available
        vol_check = vol_service.check_volatility_available()
        if not vol_check['available']:
            session.update_status('failed', f'Volatility not available: {vol_check[\"error\"]}')
            return jsonify({'error': f'Analysis engine not available: {vol_check[\"error\"]}'}), 500
        
        # Start analysis
        start_time = datetime.now()
        
        try:
            # Perform basic analysis
            analysis_results = vol_service.basic_analysis(file_path)
            
            if analysis_results['status'] == 'error':
                session.update_status('failed', f'Analysis error: {\", \".join(analysis_results[\"errors\"])}')
                return jsonify({'error': 'Analysis failed', 'details': analysis_results['errors']}), 500
            
            # Calculate analysis duration
            end_time = datetime.now()
            duration = int((end_time - start_time).total_seconds())
            
            # Create analysis result
            result = AnalysisResult(
                session_id=session.id,
                summary=f\"Analysis completed for {session.original_filename}\",
                risk_score=50  # Basic risk score for Phase 1
            )
            result.system_info = analysis_results.get('system_info', {})
            result.process_data = analysis_results.get('processes', [])
            result.network_data = analysis_results.get('network', [])
            
            db.session.add(result)
            
            # Create basic alerts
            alerts = []
            
            # Check for suspicious processes
            suspicious_processes = [p for p in analysis_results.get('processes', []) 
                                 if 'error' not in p and any(keyword in p.get('name', '').lower() 
                                 for keyword in ['cmd', 'powershell', 'suspicious'])]
            
            if suspicious_processes:
                alert = Alert(
                    session_id=session.id,
                    alert_type='suspicious_process',
                    severity='medium',
                    title='Suspicious Processes Detected',
                    description=f'Found {len(suspicious_processes)} potentially suspicious processes',
                    threat_indicators={'processes': suspicious_processes}
                )
                alerts.append(alert)
            
            # Check for network connections
            if analysis_results.get('network'):
                alert = Alert(
                    session_id=session.id,
                    alert_type='network_activity',
                    severity='low',
                    title='Network Activity Detected',
                    description=f'Found {len(analysis_results[\"network\"])} network connections',
                    threat_indicators={'connections': analysis_results['network']}
                )
                alerts.append(alert)
            
            # Save alerts
            for alert in alerts:
                db.session.add(alert)
            
            # Update session
            session.analysis_status = 'completed'
            session.analysis_duration = duration
            session.volatility_profile = analysis_results.get('profile', 'unknown')
            
            db.session.commit()
            
            return jsonify({
                'message': 'Analysis completed successfully',
                'session_id': session.id,
                'duration': duration,
                'results_summary': {
                    'processes_found': len(analysis_results.get('processes', [])),
                    'network_connections': len(analysis_results.get('network', [])),
                    'alerts_generated': len(alerts),
                    'risk_score': result.risk_score
                }
            }), 200
            
        except Exception as analysis_error:
            session.update_status('failed', str(analysis_error))
            return jsonify({'error': f'Analysis failed: {str(analysis_error)}'}), 500
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to start analysis: {str(e)}'}), 500

@analysis_bp.route('/status/<int:session_id>', methods=['GET'])
@jwt_required()
def get_analysis_status(session_id):
    \"\"\"Get analysis status\"\"\"
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        session = AnalysisSession.query.filter_by(
            id=session_id,
            user_id=user.id
        ).first()
        
        if not session:
            return jsonify({'error': 'Analysis session not found'}), 404
        
        return jsonify({
            'session': session.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get status: {str(e)}'}), 500

@analysis_bp.route('/results/<int:session_id>', methods=['GET'])
@jwt_required()
def get_analysis_results(session_id):
    \"\"\"Get analysis results\"\"\"
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        session = AnalysisSession.query.filter_by(
            id=session_id,
            user_id=user.id
        ).first()
        
        if not session:
            return jsonify({'error': 'Analysis session not found'}), 404
        
        if session.analysis_status != 'completed':
            return jsonify({'error': f'Analysis not completed. Status: {session.analysis_status}'}), 400
        
        # Get results and alerts
        result = AnalysisResult.query.filter_by(session_id=session.id).first()
        alerts = Alert.query.filter_by(session_id=session.id).all()
        
        if not result:
            return jsonify({'error': 'Analysis results not found'}), 404
        
        return jsonify({
            'session': session.to_dict(),
            'results': result.to_dict(),
            'alerts': [alert.to_dict() for alert in alerts]
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get results: {str(e)}'}), 500

@analysis_bp.route('/sessions', methods=['GET'])
@jwt_required()
def get_user_sessions():
    \"\"\"Get user's analysis sessions\"\"\"
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get query parameters
        limit = min(int(request.args.get('limit', 10)), 100)  # Max 100 sessions
        offset = int(request.args.get('offset', 0))
        status_filter = request.args.get('status')
        
        # Build query
        query = AnalysisSession.query.filter_by(user_id=user.id)
        
        if status_filter:
            query = query.filter_by(analysis_status=status_filter)
        
        query = query.order_by(AnalysisSession.upload_time.desc())
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination
        sessions = query.offset(offset).limit(limit).all()
        
        return jsonify({
            'sessions': [session.to_dict() for session in sessions],
            'total_count': total_count,
            'limit': limit,
            'offset': offset
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get sessions: {str(e)}'}), 500

@analysis_bp.route('/delete/<int:session_id>', methods=['DELETE'])
@jwt_required()
def delete_session(session_id):
    \"\"\"Delete analysis session and associated data\"\"\"
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        session = AnalysisSession.query.filter_by(
            id=session_id,
            user_id=user.id
        ).first()
        
        if not session:
            return jsonify({'error': 'Analysis session not found'}), 404
        
        # Delete associated file
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], session.filename)
        if os.path.exists(file_path):
            secure_delete_file(file_path)
        
        # Delete session (cascades to results and alerts)
        db.session.delete(session)
        db.session.commit()
        
        return jsonify({'message': 'Analysis session deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to delete session: {str(e)}'}), 500""",
}

for filename, content in phase1_api.items():
    # Create directory if needed
    if '/' in filename:
        directory = filename.split('/')[0]
        os.makedirs(directory, exist_ok=True)
    
    with open(filename, 'w') as f:
        f.write(content)
    print(f"✓ Created {filename}")

print(f"\nCreated {len(phase1_api)} API files")