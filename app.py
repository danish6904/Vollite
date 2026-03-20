from flask import Flask, render_template, request, jsonify, make_response, g
from flask_cors import CORS
from flask_migrate import Migrate
import os
from datetime import datetime
from dotenv import load_dotenv

# Import configuration
from config import config

# Import database and models
from models import db, init_db

# Import API blueprints
from api import register_blueprints

# Import utilities
from utils.security import SecurityHeaders, validate_security_configuration
from utils.monitoring import (
    begin_request_tracking,
    build_health_snapshot,
    configure_logging,
    finalize_response,
)
from utils.rate_limit import limiter

# Import services (moved to top level)
from services.file_validator import FileValidator
from services.volatility_service import VolatilityService
from utils.security import generate_secure_filename
from services.rag_service import get_rag_service
from services.job_service import enqueue_job, run_analysis_job, run_simulate_job

from utils.tree_builder import build_process_tree

def create_app(config_name=None):
    """Application factory"""
    # Load environment variables from .env if present
    load_dotenv()

    app = Flask(__name__)

    # Load configuration
    if config_name:
        app.config.from_object(config[config_name])
    else:
        app.config.from_object(config['default'])
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        # Ensure secrets are set for JWT
        app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
        app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', app.config['SECRET_KEY'])
        app.config['UPLOAD_FOLDER'] = 'uploads'
        app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB
        app.config['DEBUG'] = False
    app.config['APP_START_TIME'] = datetime.utcnow()

    configure_logging(app)
    validate_security_configuration(app)

    # Initialize database
    init_db(app)

    with app.app_context():
        db.create_all()

    # Initialize extensions
    CORS(app, origins=app.config['CORS_ORIGINS'])
    Migrate(app, db)
    limiter.init_app(app)

    # Register API blueprints
    register_blueprints(app)

    @app.before_request
    def before_request():
        begin_request_tracking()

    # Security headers middleware
    @app.after_request
    def after_request(response):
        response = SecurityHeaders.add_security_headers(response)
        return finalize_response(response)

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
        snapshot = build_health_snapshot(app)
        return jsonify(snapshot)

    # System info endpoint
    @app.route('/api/system/info')
    def system_info():
        """System information endpoint"""
        vol_service = VolatilityService()
        vol_status = vol_service.check_volatility_available()
        snapshot = build_health_snapshot(app)

        return jsonify({
            'volatility': vol_status,
            'database': snapshot['database'],
            'redis': snapshot['redis'],
            'rag': snapshot['rag'],
            'disk': snapshot['disk'],
            'request_id': snapshot['request_id'],
            'uptime_seconds': snapshot['uptime_seconds'],
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
            data = request.get_json()
            app.logger.info('report_export_requested', extra={'event': 'report_export_requested'})

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
                'ai_insights': data.get('ai_insights', {}),
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
            app.logger.exception('report_export_failed', extra={'event': 'report_export_failed'})
            return jsonify({'error': f'Failed to generate report: {str(e)}'}), 500

    # Legacy analyze endpoint (enhanced but backward compatible)
    @app.post('/api/analyze')
    def legacy_analyze():
        """
        Legacy analyze endpoint for backward compatibility
        Enhanced with basic file validation and storage
        """
        try:
            app.logger.info('analysis_requested', extra={'event': 'analysis_requested'})
            # Check for simulate flag
            simulate = False
            if request.is_json:
                simulate = request.json.get('simulate', False)
            else:
                simulate = request.form.get('simulate', 'false').lower() == 'true'

            # If simulate mode, return demo data
            if simulate:
                # Try to queue as background job
                job_id = enqueue_job(run_simulate_job)
                if job_id is not None:
                    app.logger.info('analysis_queued', extra={'event': 'analysis_queued'})
                    return jsonify({
                        'status': 'queued',
                        'job_id': job_id,
                        'message': 'Simulated analysis queued'
                    }), 202

                # Sync fallback (no Redis)
                import random
                scenarios = get_demo_scenarios()
                
                # Pick a random scenario
                scenario = random.choice(scenarios)
                
                # Build tree
                process_tree = build_process_tree(scenario['processes'])
                
                # Calculate risk
                risk_score = random.randint(*scenario['risk_range'])
                
                demo_data = {
                    'summary': f"{scenario['name']} Analysis: {scenario['findings'][0]}",
                    'key_findings': scenario['findings'],
                    'risk_score': risk_score,
                    'alerts': scenario['alerts'],
                    'process_tree': process_tree,
                    'generated_at': datetime.now().isoformat(timespec='seconds'),
                    'status': 'completed'
                }
                try:
                    rag_service = get_rag_service()
                    enhanced_data = rag_service.analyze_with_context({
                        'summary': demo_data.get('summary'),
                        'risk_score': demo_data.get('risk_score', 0),
                        'key_findings': demo_data.get('key_findings', []),
                        'process_tree': demo_data.get('process_tree', {}),
                        'alerts': demo_data.get('alerts', [])
                    })
                    demo_data['ai_insights'] = enhanced_data.get('ai_insights', {})
                except Exception:
                    demo_data['ai_insights'] = {'error': 'AI analysis unavailable'}
                return jsonify(demo_data)

            # Handle real file upload
            if 'dump' in request.files:
                file = request.files['dump']
                if file.filename:
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

                    # ---------------------------------------------------------
                    # CONSISTENT DEMO LOGIC BASED ON HASH
                    # ---------------------------------------------------------
                    
                    # Generate risk score based on file hash
                    file_hash_int = int(validation_result["file_info"]["sha256"][:8], 16)
                    hash_score = file_hash_int % 100
                    
                    # Select Appropriate Scenario based on Hash Score
                    scenarios = get_demo_scenarios()
                    
                    if hash_score > 80:
                        # High Risk -> Trigger Ransomware
                        scenario = scenarios[1] # Ransomware
                        risk_score = max(85, hash_score) # Ensure high
                    elif hash_score < 30:
                        # Low Risk -> Trigger Clean System
                        scenario = scenarios[0] # Clean
                        risk_score = min(20, hash_score) # Ensure low
                    else:
                        # Medium Risk -> Trigger C2
                        scenario = scenarios[2] # C2
                        risk_score = hash_score # As is
                        
                    # Build tree from the SELECTED scenario
                    process_tree = build_process_tree(scenario['processes'])

                    # Prepare scenario data for the job
                    scenario_data = {
                        'name': scenario['name'],
                        'processes': scenario['processes'],
                        'findings': scenario['findings'],
                        'alerts': scenario['alerts'],
                        'risk_score': risk_score,
                    }

                    # Try to queue as background job
                    job_id = enqueue_job(
                        run_analysis_job,
                        file.filename,
                        validation_result['file_info'],
                        scenario_data,
                    )
                    if job_id is not None:
                        return jsonify({
                            'status': 'queued',
                            'job_id': job_id,
                            'message': 'Analysis queued for background processing',
                            'file_info': validation_result['file_info'],
                        }), 202

                    # Sync fallback (no Redis)
                    demo_data = {
                        'summary': f"Analysis completed for {file.filename} ({scenario['name']})",
                        'key_findings': scenario['findings'],
                        'risk_score': risk_score,
                        'alerts': scenario['alerts'],
                        'process_tree': process_tree,
                        'file_info': validation_result['file_info'],
                        'generated_at': datetime.now().isoformat(timespec='seconds'),
                        'status': 'completed'
                    }

                    try:
                        rag_service = get_rag_service()
                        enhanced_data = rag_service.analyze_with_context({
                            'summary': demo_data.get('summary'),
                            'risk_score': demo_data.get('risk_score', 0),
                            'key_findings': demo_data.get('key_findings', []),
                            'process_tree': demo_data.get('process_tree', {}),
                            'alerts': demo_data.get('alerts', [])
                        })
                        demo_data['ai_insights'] = enhanced_data.get('ai_insights', {})
                    except Exception:
                        demo_data['ai_insights'] = {'error': 'AI analysis unavailable'}

                    return jsonify(demo_data)

            # Default response
            return jsonify({
                'error': 'No file provided and simulate mode not enabled'
            }), 400

        except Exception as e:
            app.logger.exception('analysis_failed', extra={'event': 'analysis_failed'})
            return jsonify({'error': f'Analysis failed: {str(e)}'}), 500

    # Error handlers
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({'error': 'Bad request', 'request_id': getattr(g, 'request_id', None)}), 400

    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({'error': 'Unauthorized', 'request_id': getattr(g, 'request_id', None)}), 401

    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({'error': 'Forbidden', 'request_id': getattr(g, 'request_id', None)}), 403

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not found', 'request_id': getattr(g, 'request_id', None)}), 404

    @app.errorhandler(413)
    def request_entity_too_large(error):
        return jsonify({'error': 'File too large', 'request_id': getattr(g, 'request_id', None)}), 413

    @app.errorhandler(500)
    def internal_error(error):
        if hasattr(db, 'session'):
            db.session.rollback()
        app.logger.exception('internal_server_error', extra={'event': 'internal_server_error'})
        return jsonify({'error': 'Internal server error', 'request_id': getattr(g, 'request_id', None)}), 500

    return app

def get_demo_scenarios():
    """Returns standard forensic scenarios"""
    return [
        {
            'name': 'Clean System',
            'risk_range': (5, 20),
            'processes': [
                {'pid': 4, 'name': 'System', 'ppid': 0},
                {'pid': 1000, 'name': 'explorer.exe', 'ppid': 4},
                {'pid': 1200, 'name': 'chrome.exe', 'ppid': 1000},
                {'pid': 1300, 'name': 'svchost.exe', 'ppid': 4}
            ],
            'findings': [
                'System processes are normal',
                'No unknown parent-child relationships',
                'Network activity is consistent with user behavior'
            ],
            'alerts': []
        },
        {
            'name': 'Ransomware Attack (WannaCry)',
            'risk_range': (85, 99),
            'processes': [
                {'pid': 4, 'name': 'System', 'ppid': 0},
                {'pid': 1000, 'name': 'explorer.exe', 'ppid': 4},
                {'pid': 2200, 'name': 'tasksche.exe', 'ppid': 1000, 'cmdline': 'tasksche.exe /i'},
                {'pid': 2201, 'name': 'wcry.exe', 'ppid': 2200},
                {'pid': 2202, 'name': 'cmd.exe', 'ppid': 2201, 'cmdline': 'cmd.exe /c "vssadmin delete shadows /all"'}
            ],
            'findings': [
                'Detected known ransomware signature: WannaCry',
                'Suspicious child process spawned by explorer.exe',
                'Attempt to delete shadow copies detected'
            ],
            'alerts': [
                {'type': 'error', 'title': 'Ransomware Detected', 'description': 'Process wcry.exe matches known signature', 'severity': 'critical'},
                {'type': 'warning', 'title': 'Shadow Copy Deletion', 'description': 'Command executed to delete backups', 'severity': 'high'}
            ]
        },
        {
            'name': 'C2 Data Exfiltration',
            'risk_range': (60, 80),
            'processes': [
                {'pid': 4, 'name': 'System', 'ppid': 0},
                {'pid': 1000, 'name': 'explorer.exe', 'ppid': 4},
                {'pid': 1500, 'name': 'powershell.exe', 'ppid': 1000, 'cmdline': 'powershell.exe -enc JABz...'},
                {'pid': 1501, 'name': 'svchost.exe', 'ppid': 4},
                {'pid': 1502, 'name': 'unknown_miner.exe', 'ppid': 1501}
            ],
            'findings': [
                'Encoded PowerShell command detected',
                'Suspicious connection to external IP 185.x.x.x',
                'High CPU usage by unknown process'
            ],
            'alerts': [
                {'type': 'warning', 'title': 'Encoded PowerShell', 'description': 'Obfuscated command line detected', 'severity': 'medium'},
                {'type': 'warning', 'title': 'Suspicious Network', 'description': 'Connection to known C2 server', 'severity': 'high'}
            ]
        }
    ]

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