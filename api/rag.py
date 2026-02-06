"""
RAG API Endpoints for Enhanced AI Analysis
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.rag_service import get_rag_service
from models.analysis import AnalysisSession
from models import db
from datetime import datetime
import logging

rag_bp = Blueprint('rag', __name__, url_prefix='/api/rag')
logger = logging.getLogger(__name__)


@rag_bp.route('/explain', methods=['POST'])
@jwt_required()
def explain_finding():
    """
    Explain a specific finding using AI
    
    POST /api/rag/explain
    {
        "finding": "Suspicious process detected"
    }
    """
    try:
        data = request.get_json()
        finding = data.get('finding')
        
        if not finding:
            return jsonify({'error': 'Finding text is required'}), 400
        
        rag_service = get_rag_service()
        
        if not rag_service.available:
            return jsonify({
                'error': 'RAG service not available',
                'explanation': 'AI explanation features require additional dependencies'
            }), 503
        
        explanation = rag_service.explain_finding(finding)
        
        return jsonify({
            'finding': finding,
            'explanation': explanation,
            'timestamp': datetime.utcnow().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Failed to explain finding: {e}")
        return jsonify({'error': str(e)}), 500


@rag_bp.route('/recommendations/<int:analysis_id>', methods=['GET'])
@jwt_required()
def get_recommendations(analysis_id):
    """
    Get AI-powered recommendations for an analysis
    
    GET /api/rag/recommendations/<analysis_id>
    """
    try:
        user_id = get_jwt_identity()
        
        # Get analysis session
        analysis = AnalysisSession.query.filter_by(
            id=analysis_id,
            user_id=user_id
        ).first()
        
        if not analysis:
            return jsonify({'error': 'Analysis not found'}), 404
        
        # Convert to dict
        analysis_data = analysis.to_dict()
        
        rag_service = get_rag_service()
        recommendations = rag_service.get_recommendations(analysis_data)
        
        return jsonify({
            'analysis_id': analysis_id,
            'recommendations': recommendations,
            'timestamp': datetime.utcnow().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Failed to generate recommendations: {e}")
        return jsonify({'error': str(e)}), 500


@rag_bp.route('/similar-cases', methods=['POST'])
@jwt_required()
def find_similar_cases():
    """
    Find similar historical cases
    
    POST /api/rag/similar-cases
    {
        "query": "ransomware encryption process",
        "limit": 5
    }
    """
    try:
        data = request.get_json()
        query = data.get('query')
        limit = data.get('limit', 5)
        
        if not query:
            return jsonify({'error': 'Query is required'}), 400
        
        rag_service = get_rag_service()
        
        if not rag_service.available:
            return jsonify({
                'error': 'RAG service not available',
                'message': 'Historical case search requires additional dependencies'
            }), 503
        
        similar_cases = rag_service.query_similar_cases(query, k=limit)
        
        return jsonify({
            'query': query,
            'similar_cases': similar_cases,
            'count': len(similar_cases),
            'timestamp': datetime.utcnow().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Failed to find similar cases: {e}")
        return jsonify({'error': str(e)}), 500


@rag_bp.route('/enhance-analysis/<int:analysis_id>', methods=['POST'])
@jwt_required()
def enhance_analysis():
    """
    Enhance analysis with AI insights
    
    POST /api/rag/enhance-analysis/<analysis_id>
    """
    try:
        user_id = get_jwt_identity()
        analysis_id = request.view_args['analysis_id']
        
        # Get analysis session
        analysis = AnalysisSession.query.filter_by(
            id=analysis_id,
            user_id=user_id
        ).first()
        
        if not analysis:
            return jsonify({'error': 'Analysis not found'}), 404
        
        # Convert to dict
        analysis_data = analysis.to_dict()
        
        rag_service = get_rag_service()
        
        if not rag_service.available:
            return jsonify({
                'error': 'RAG service not available',
                'message': 'AI enhancement requires additional dependencies'
            }), 503
        
        # Enhance with AI context
        enhanced_data = rag_service.analyze_with_context(analysis_data)
        
        return jsonify({
            'analysis_id': analysis_id,
            'ai_insights': enhanced_data.get('ai_insights', {}),
            'timestamp': datetime.utcnow().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Failed to enhance analysis: {e}")
        return jsonify({'error': str(e)}), 500


@rag_bp.route('/generate-summary/<int:analysis_id>', methods=['POST'])
@jwt_required()
def generate_summary(analysis_id):
    """
    Generate AI-powered executive summary
    
    POST /api/rag/generate-summary/<analysis_id>
    """
    try:
        user_id = get_jwt_identity()
        
        # Get analysis session
        analysis = AnalysisSession.query.filter_by(
            id=analysis_id,
            user_id=user_id
        ).first()
        
        if not analysis:
            return jsonify({'error': 'Analysis not found'}), 404
        
        # Convert to dict
        analysis_data = analysis.to_dict()
        
        rag_service = get_rag_service()
        
        if not rag_service.available:
            return jsonify({
                'error': 'RAG service not available',
                'message': 'Summary generation requires additional dependencies'
            }), 503
        
        summary = rag_service.generate_report_summary(analysis_data)
        
        return jsonify({
            'analysis_id': analysis_id,
            'summary': summary,
            'timestamp': datetime.utcnow().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Failed to generate summary: {e}")
        return jsonify({'error': str(e)}), 500


@rag_bp.route('/status', methods=['GET'])
def get_rag_status():
    """
    Get RAG service status
    
    GET /api/rag/status
    """
    try:
        rag_service = get_rag_service()
        
        return jsonify({
            'available': rag_service.available,
            'model': rag_service.model_name if rag_service.available else None,
            'embedding_model': rag_service.embedding_model if rag_service.available else None,
            'vector_store_initialized': rag_service.vector_store is not None if rag_service.available else False
        })
    
    except Exception as e:
        logger.error(f"Failed to get RAG status: {e}")
        return jsonify({'error': str(e)}), 500
