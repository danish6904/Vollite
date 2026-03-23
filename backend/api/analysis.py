from flask import Blueprint, request, jsonify, current_app
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
from services.risk_analyzer import RiskAnalyzer
from services.rag_service import get_rag_service
from utils.security import generate_secure_filename, secure_delete_file

analysis_bp = Blueprint('analysis', __name__)

def get_current_user():
    """Get current authenticated user"""
    user_id = get_jwt_identity()
    try:
        user_id = int(user_id)
    except (TypeError, ValueError):
        return None
    return User.query.filter_by(id=user_id, is_active=True).first()

@analysis_bp.route('/upload', methods=['POST'])
@jwt_required()
def upload_file():
    """Upload memory dump file"""
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
    """Start memory dump analysis"""
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

        # Optional plugin selection from request
        requested_plugins = []
        extra_args = []
        if request.is_json:
            data = request.get_json(silent=True) or {}
            requested_plugins = data.get('plugins', []) or []
            extra_args = data.get('plugin_args', []) or []

        # Check if Volatility is available
        vol_check = vol_service.check_volatility_available()
        if not vol_check['available'] and not requested_plugins:
            # Graceful fallback: perform simulated basic analysis so flow continues
            start_time = datetime.now()

            # Simulated minimal analysis data
            simulated_processes = []
            simulated_network = []
            simulated_system_info = {
                'note': 'Simulated analysis because Volatility engine is not available'
            }

            # Calculate duration
            end_time = datetime.now()
            duration = int((end_time - start_time).total_seconds())

            # Use RiskAnalyzer for simulated analysis too
            risk_analyzer = RiskAnalyzer()
            simulated_data = {
                'processes': simulated_processes,
                'connections': simulated_network,
                'system_info': simulated_system_info
            }
            risk_analysis = risk_analyzer.analyze_risk(simulated_data, simulated_data, simulated_system_info)
            risk_quantification = risk_analyzer.quantify_total_risk(risk_analysis, {})
            
            # Create analysis result (simulated) with enhanced risk score
            result = AnalysisResult(
                session_id=session.id,
                summary=f"Simulated analysis for {session.original_filename}",
                risk_score=risk_quantification['final']['score']
            )
            result.system_info = simulated_system_info
            result.process_data = simulated_processes
            result.network_data = simulated_network
            
            # Add AI insights
            try:
                rag_service = get_rag_service()
                
                # Prepare data for RAG
                rag_data = {
                    'summary': result.summary,
                    'risk_score': result.risk_score,
                    'key_findings': [
                        f"Risk Score: {result.risk_score}/100",
                        "Simulated analysis due to missing engine"
                    ],
                    'process_tree': {'processes': simulated_processes},
                    'alerts': [] 
                }
                
                # Get AI insights
                enhanced_data = rag_service.analyze_with_context(rag_data)
                result.ai_insights = enhanced_data.get('ai_insights', {})
                
            except Exception as e:
                current_app.logger.warning(f"RAG analysis failed: {e}")
                result.ai_insights = {'error': 'AI analysis unavailable'}

            risk_quantification = risk_analyzer.quantify_total_risk(risk_analysis, result.ai_insights)
            result.risk_score = risk_quantification['final']['score']
            if isinstance(result.ai_insights, dict):
                result.ai_insights['risk_quantification'] = risk_quantification
            else:
                result.ai_insights = {'summary': str(result.ai_insights), 'risk_quantification': risk_quantification}

            db.session.add(result)

            # Add informational alert
            alert = Alert(
                session_id=session.id,
                alert_type='engine_unavailable',
                severity='low',
                title='Volatility Not Available',
                description=vol_check.get('error') or 'Volatility engine not found on host',
                threat_indicators={}
            )
            db.session.add(alert)

            # Update session as completed (simulated)
            session.analysis_status = 'completed'
            session.analysis_duration = duration
            session.volatility_profile = 'unknown'

            db.session.commit()

            return jsonify({
                'message': 'Simulated analysis completed (engine unavailable)',
                'session_id': session.id,
                'duration': duration,
                'results_summary': {
                    'processes_found': 0,
                    'network_connections': 0,
                    'alerts_generated': 1,
                    'risk_score': result.risk_score,
                    'activity_risk_score': risk_quantification['activity']['score'],
                    'llm_risk_score': risk_quantification['llm']['score']
                }
            }), 200

        # Start analysis
        start_time = datetime.now()

        try:
            # If specific plugins requested, run them; else perform basic analysis
            if requested_plugins:
                plugin_outputs = vol_service.run_plugins(file_path, requested_plugins, extra_args)
                # Store raw plugin outputs in results
                analysis_results = {
                    'profile': 'unknown',
                    'system_info': {},
                    'processes': [],
                    'network': [],
                    'status': 'success',
                    'errors': []
                }
            else:
                analysis_results = vol_service.basic_analysis(file_path)

            if analysis_results['status'] == 'error':
                session.update_status('failed', f'Analysis error: {", ".join(analysis_results["errors"])}')
                return jsonify({'error': 'Analysis failed', 'details': analysis_results['errors']}), 500

            # Calculate analysis duration
            end_time = datetime.now()
            duration = int((end_time - start_time).total_seconds())

            # Prepare data for risk analysis
            if requested_plugins:
                # For plugin-based analysis, structure the data
                process_data = {'processes': plugin_outputs if isinstance(plugin_outputs, list) else []}
                network_data = {'connections': []}
                system_info = {'plugins': requested_plugins}
            else:
                process_data = {'processes': analysis_results.get('processes', [])}
                network_data = {'connections': analysis_results.get('network', [])}
                system_info = analysis_results.get('system_info', {})

            # Use RiskAnalyzer for enhanced risk scoring
            risk_analyzer = RiskAnalyzer()
            risk_analysis = risk_analyzer.analyze_risk(process_data, network_data, system_info)
            risk_quantification = risk_analyzer.quantify_total_risk(risk_analysis, {})
            
            # Create analysis result with enhanced risk score
            result = AnalysisResult(
                session_id=session.id,
                summary=f"Analysis completed for {session.original_filename}",
                risk_score=risk_quantification['final']['score']
            )
            
            # Store the analysis data
            result.system_info = system_info
            result.process_data = process_data['processes']
            result.network_data = network_data['connections']

            # Create basic alerts first (needed for RAG context)
            alerts = []
            
            suspicious_processes = [p for p in analysis_results.get('processes', []) 
                                 if isinstance(p, dict) and 'error' not in p and any(keyword in p.get('name', '').lower() 
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
                    description=f'Found {len(analysis_results["network"])} network connections',
                    threat_indicators={'connections': analysis_results['network']}
                )
                alerts.append(alert)

            # Add AI insights
            try:
                rag_service = get_rag_service()
                
                # Prepare data for RAG including alerts
                rag_data = {
                    'summary': result.summary,
                    'risk_score': result.risk_score,
                    'key_findings': [
                        f"Risk Score: {result.risk_score}/100",
                        f"Found {len(suspicious_processes)} suspicious processes"
                    ],
                    'process_tree': {'processes': result.process_data},
                    'alerts': [a.to_dict() for a in alerts]
                }
                
                # Get AI insights
                enhanced_data = rag_service.analyze_with_context(rag_data)
                result.ai_insights = enhanced_data.get('ai_insights', {})
                
            except Exception as e:
                current_app.logger.warning(f"RAG analysis failed: {e}")
                result.ai_insights = {'error': 'AI analysis unavailable'}

            risk_quantification = risk_analyzer.quantify_total_risk(risk_analysis, result.ai_insights)
            result.risk_score = risk_quantification['final']['score']
            if isinstance(result.ai_insights, dict):
                result.ai_insights['risk_quantification'] = risk_quantification
            else:
                result.ai_insights = {'summary': str(result.ai_insights), 'risk_quantification': risk_quantification}

            db.session.add(result)

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
                    'risk_score': result.risk_score,
                    'activity_risk_score': risk_quantification['activity']['score'],
                    'llm_risk_score': risk_quantification['llm']['score']
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
    """Get analysis status"""
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
    """Get analysis results"""
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
    """Get user's analysis sessions"""
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
    """Delete analysis session and associated data"""
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
        return jsonify({'error': f'Failed to delete session: {str(e)}'}), 500