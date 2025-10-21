from flask import Flask, render_template, request, jsonify, make_response
from flask_cors import CORS
from flask_migrate import Migrate
import os
from datetime import datetime

# Import configuration
from config import config

# Import database and models
from models import init_db, db
from models.user import User
from models.analysis import AnalysisSession, AnalysisResult, Alert

# Import API blueprints
from api import register_blueprints

# Import utilities
from utils.database import init_database, check_database_connection
from utils.security import SecurityHeaders

def create_app(config_name=None):
    """Application factory"""
    app = Flask(__name__)

    # Load configuration
    config_name = config_name or os.environ.get('FLASK_ENV', 'development')
    app.config.from_object(config[config_name])

    # Initialize extensions
    init_db(app)
    CORS(app, origins=app.config['CORS_ORIGINS'])
    migrate = Migrate(app, db)

    # Register API blueprints
    register_blueprints(app)

    # Initialize database
    with app.app_context():
        init_database()

    # Security headers middleware
    @app.after_request
    def after_request(response):
        return SecurityHeaders.add_security_headers(response)

    # Original frontend routes
    @app.route('/')
    def home():
        return render_template('home.html')

    @app.route('/about')
    def about():
        return render_template('about.html')

    @app.route('/contact')
    def contact():
        return render_template('contact.html')

    @app.route('/dashboard')
    def dashboard():
        return render_template('dashboard.html')

    # Health check endpoint
    @app.route('/api/health')
    def health_check():
        """Health check endpoint"""
        db_status = check_database_connection()
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'database': db_status['status'],
            'version': '1.0.0-phase1'
        })

    # System info endpoint
    @app.route('/api/system/info')
    def system_info():
        """System information endpoint"""
        from services.volatility_service import VolatilityService

        vol_service = VolatilityService()
        vol_status = vol_service.check_volatility_available()

        return jsonify({
            'volatility': vol_status,
            'database': check_database_connection(),
            'upload_folder': app.config['UPLOAD_FOLDER'],
            'max_file_size': app.config['MAX_CONTENT_LENGTH']
        })

    # Enhanced export report endpoint (compatible with existing frontend)
    @app.post('/export_report')
    def export_report():
        """
        Enhanced export report endpoint (backward compatible)
        Accepts JSON payload with analysis data and returns HTML report
        """
        try:
            data = request.get_json(force=True)

            # Create enhanced report data
            report_data = {
                'title': 'volLite Forensic Report',
                'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'summary': data.get('summary', 'No summary available'),
                'findings': data.get('key_findings', []),
                'risk_score': data.get('risk_score', 0),
                'alerts': data.get('alerts', []),
                'process_tree': data.get('process_tree', {}),
                'system_info': data.get('system_info', {}),
                'analysis_duration': data.get('analysis_duration', 'N/A'),
                'file_info': data.get('file_info', {})
            }

            # Render HTML report
            html = render_template('report.html', **report_data)

            # Return as attachment
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'volLite_report_{timestamp}.html'

            response = make_response(html)
            response.headers['Content-Type'] = 'text/html; charset=utf-8'
            response.headers['Content-Disposition'] = f'attachment; filename={filename}'

            return response

        except Exception as e:
            return jsonify({'error': f'Failed to generate report: {str(e)}'}), 500

    # Legacy analyze endpoint (enhanced but backward compatible)
    @app.post('/api/analyze')
    def legacy_analyze():
        """
        Legacy analyze endpoint for backward compatibility
        Enhanced with basic file validation and storage
        """
        try:
            # Check for simulate flag
            simulate = False
            if request.is_json:
                simulate = request.json.get('simulate', False)
            else:
                simulate = request.form.get('simulate', 'false').lower() == 'true'

            # If simulate mode, return demo data
            if simulate:
                # Load demo data (you'll need to create these files)
                demo_data = {
                    'summary': 'Demo analysis completed successfully',
                    'key_findings': [
                        'System appears to be Windows 10 x64',
                        'Multiple processes detected',
                        'Network activity present'
                    ],
                    'risk_score': 35,
                    'alerts': [
                        {
                            'type': 'info',
                            'title': 'Demo Alert',
                            'description': 'This is a demonstration alert',
                            'severity': 'low'
                        }
                    ],
                    'process_tree': {
                        'processes': [
                            {'pid': 4, 'name': 'System', 'ppid': 0},
                            {'pid': 1000, 'name': 'explorer.exe', 'ppid': 4}
                        ]
                    },
                    'generated_at': datetime.now().isoformat(timespec='seconds'),
                    'status': 'completed'
                }
                return jsonify(demo_data)

            # Handle real file upload
            if 'dump' in request.files:
                file = request.files['dump']
                if file.filename:
                    # Use the new file validation system
                    from services.file_validator import FileValidator
                    from utils.security import generate_secure_filename

                    # Generate secure filename
                    secure_name = generate_secure_filename(file.filename, 'legacy')

                    # Save file
                    upload_folder = app.config['UPLOAD_FOLDER']
                    os.makedirs(upload_folder, exist_ok=True)
                    file_path = os.path.join(upload_folder, secure_name)
                    file.save(file_path)

                    # Validate file
                    validator = FileValidator()
                    validation_result = validator.validate_file(file, file_path)

                    if not validation_result['valid']:
                        # Clean up invalid file
                        if os.path.exists(file_path):
                            os.remove(file_path)

                        return jsonify({
                            'error': 'File validation failed',
                            'details': validation_result['errors']
                        }), 400

                    # For Phase 1, return enhanced demo data with file info
                    demo_data = {
                        'summary': f'Analysis completed for {file.filename}',
                        'key_findings': [
                            f'File size: {validation_result["file_info"]["file_size"]} bytes',
                            f'File hash: {validation_result["file_info"]["sha256"][:16]}...',
                            'Basic validation passed'
                        ],
                        'risk_score': 25,
                        'alerts': [
                            {
                                'type': 'info',
                                'title': 'File Processed',
                                'description': f'Successfully processed {file.filename}',
                                'severity': 'low'
                            }
                        ],
                        'process_tree': {'processes': []},
                        'file_info': validation_result['file_info'],
                        'generated_at': datetime.now().isoformat(timespec='seconds'),
                        'status': 'completed'
                    }

                    return jsonify(demo_data)

            # Default response
            return jsonify({
                'error': 'No file provided and simulate mode not enabled'
            }), 400

        except Exception as e:
            return jsonify({'error': f'Analysis failed: {str(e)}'}), 500

    # Error handlers
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({'error': 'Bad request'}), 400

    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({'error': 'Unauthorized'}), 401

    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({'error': 'Forbidden'}), 403

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not found'}), 404

    @app.errorhandler(413)
    def request_entity_too_large(error):
        return jsonify({'error': 'File too large'}), 413

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

    return app

# Create app instance
app = create_app()

if __name__ == '__main__':
    # Create upload directory
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Run application
    app.run(
        debug=app.config.get('DEBUG', False),
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000))
    )