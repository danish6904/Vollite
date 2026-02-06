
# Enhanced analysis endpoints for detailed risk analysis
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

from models import db
from models.analysis import AnalysisSession, AnalysisResult
from services.risk_analyzer import RiskAnalyzer

# Create blueprint for enhanced analysis endpoints
enhanced_analysis_bp = Blueprint('enhanced_analysis', __name__)

@enhanced_analysis_bp.route('/detailed/<int:session_id>', methods=['GET'])
@jwt_required()
def get_detailed_analysis(session_id):
    '''Get detailed risk analysis with explanations'''
    try:
        # Get analysis session
        session = AnalysisSession.query.get_or_404(session_id)

        # Verify user owns this session
        if session.user_id != get_jwt_identity():
            return jsonify({'error': 'Access denied'}), 403

        # Get analysis results
        result = AnalysisResult.query.filter_by(session_id=session_id).first()
        if not result:
            return jsonify({'error': 'Analysis results not found'}), 404

        # Perform detailed risk analysis
        analyzer = RiskAnalyzer()
        detailed_analysis = analyzer.analyze_risk(
            process_data=result.process_data or {},
            network_data=result.network_data or {},
            system_info=result.system_info or {}
        )

        return jsonify({
            'session_id': session_id,
            'analysis_status': session.analysis_status,
            'original_risk_score': result.risk_score,
            'detailed_analysis': detailed_analysis,
            'generated_at': datetime.utcnow().isoformat()
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@enhanced_analysis_bp.route('/explain/<int:session_id>', methods=['GET'])  
@jwt_required()
def explain_risk_score(session_id):
    '''Get human-readable explanation of risk score'''
    try:
        # Get analysis results
        result = AnalysisResult.query.filter_by(session_id=session_id).first()
        if not result:
            return jsonify({'error': 'Analysis results not found'}), 404

        # Perform risk analysis
        analyzer = RiskAnalyzer()
        analysis = analyzer.analyze_risk(
            process_data=result.process_data or {},
            network_data=result.network_data or {},
            system_info=result.system_info or {}
        )

        return jsonify({
            'risk_score': analysis['risk_score'],
            'risk_level': analysis['risk_level'], 
            'confidence': analysis['confidence'],
            'explanation': analysis['explanation'],
            'breakdown': analysis['breakdown'],
            'recommendations': analysis['recommendations'],
            'factor_count': len(analysis['risk_factors'])
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500
