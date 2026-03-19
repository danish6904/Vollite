"""
Job status API endpoints
Provides polling endpoint for background job results
"""

from flask import Blueprint, jsonify
from services.job_service import get_job_status, is_redis_available

jobs_bp = Blueprint('jobs', __name__)


@jobs_bp.route('/status/<job_id>', methods=['GET'])
def job_status(job_id):
    """Poll for job status and result"""
    result = get_job_status(job_id)
    status = result.get('status')

    if status == 'not_found':
        return jsonify(result), 404
    if status == 'error':
        return jsonify(result), 503

    return jsonify(result), 200


@jobs_bp.route('/health', methods=['GET'])
def jobs_health():
    """Check if the job queue backend (Redis) is available"""
    available = is_redis_available()
    return jsonify({
        'redis_available': available,
        'background_jobs': 'enabled' if available else 'disabled (sync fallback)',
    }), 200 if available else 503
