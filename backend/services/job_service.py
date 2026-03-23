"""
Background Job Service using Redis + threading
Lightweight, Windows-compatible alternative to RQ/Celery.
Falls back to synchronous execution when Redis is unavailable.
"""

import os
import json
import uuid
import logging
import threading
import traceback
from datetime import datetime
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# --- Redis availability ---
try:
    import redis as _redis_mod
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("redis package not installed. Background jobs disabled.")


# ---------------------------------------------------------------------------
# Redis helpers
# ---------------------------------------------------------------------------

def get_redis_connection():
    """Get Redis connection using config from environment"""
    if not REDIS_AVAILABLE:
        return None
    try:
        socket_timeout = float(os.getenv('REDIS_SOCKET_TIMEOUT', '0.2'))
        conn = _redis_mod.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            db=int(os.getenv('REDIS_DB', 0)),
            password=os.getenv('REDIS_PASSWORD') or None,
            socket_connect_timeout=socket_timeout,
            socket_timeout=socket_timeout,
            decode_responses=True,
        )
        conn.ping()
        return conn
    except Exception as e:
        logger.debug(f"Redis not available: {e}")
        return None


def is_redis_available() -> bool:
    """Quick check whether Redis is reachable."""
    return get_redis_connection() is not None


# ---------------------------------------------------------------------------
# Lightweight job queue backed by Redis hashes
# ---------------------------------------------------------------------------

_JOB_PREFIX = "vollite:job:"


def _job_key(job_id: str) -> str:
    return f"{_JOB_PREFIX}{job_id}"


def enqueue_job(func, *args, **kwargs) -> Optional[str]:
    """
    Queue a job for background execution.
    Returns a job_id if Redis is available, None otherwise.
    """
    conn = get_redis_connection()
    if conn is None:
        return None

    job_id = str(uuid.uuid4())
    conn.hset(_job_key(job_id), mapping={
        'status': 'queued',
        'created_at': datetime.utcnow().isoformat(),
        'result': '',
        'error': '',
    })
    # Expire job data after 1 hour
    conn.expire(_job_key(job_id), 3600)

    # Run the job in a background thread
    t = threading.Thread(
        target=_execute_job,
        args=(job_id, func, args, kwargs),
        daemon=True,
    )
    t.start()
    return job_id


def _execute_job(job_id: str, func, args, kwargs):
    """Worker thread: execute the job and store result in Redis."""
    conn = get_redis_connection()
    if conn is None:
        return

    try:
        conn.hset(_job_key(job_id), 'status', 'started')
        result = func(*args, **kwargs)
        conn.hset(_job_key(job_id), mapping={
            'status': 'finished',
            'result': json.dumps(result, default=str),
        })
    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}")
        conn.hset(_job_key(job_id), mapping={
            'status': 'failed',
            'error': traceback.format_exc(),
        })


def get_job_status(job_id: str) -> Dict[str, Any]:
    """
    Return the current status of a job.
    Returns dict with keys: job_id, status, result (if finished), error (if failed).
    """
    conn = get_redis_connection()
    if conn is None:
        return {'job_id': job_id, 'status': 'error', 'error': 'Redis unavailable'}

    data = conn.hgetall(_job_key(job_id))
    if not data:
        return {'job_id': job_id, 'status': 'not_found'}

    payload: Dict[str, Any] = {
        'job_id': job_id,
        'status': data.get('status', 'unknown'),
    }

    if payload['status'] == 'finished' and data.get('result'):
        payload['result'] = json.loads(data['result'])
    elif payload['status'] == 'failed' and data.get('error'):
        payload['error'] = data['error']

    return payload


# ---------------------------------------------------------------------------
# Job functions
# ---------------------------------------------------------------------------

def run_analysis_job(original_filename: str, file_info: dict,
                     scenario_data: dict) -> Dict[str, Any]:
    """
    Background job: run analysis + RAG enrichment.
    """
    from services.rag_service import get_rag_service
    from services.risk_analyzer import RiskAnalyzer
    from utils.tree_builder import build_process_tree

    start = datetime.now()

    process_tree = build_process_tree(scenario_data['processes'])
    risk_score = scenario_data['risk_score']

    demo_data: Dict[str, Any] = {
        'summary': f"Analysis completed for {original_filename} ({scenario_data['name']})",
        'key_findings': scenario_data['findings'],
        'risk_score': risk_score,
        'alerts': scenario_data['alerts'],
        'process_tree': process_tree,
        'file_info': file_info,
        'generated_at': datetime.now().isoformat(timespec='seconds'),
        'status': 'completed',
    }

    try:
        rag_service = get_rag_service()
        enhanced = rag_service.analyze_with_context({
            'summary': demo_data['summary'],
            'risk_score': demo_data['risk_score'],
            'key_findings': demo_data['key_findings'],
            'process_tree': demo_data['process_tree'],
            'alerts': demo_data['alerts'],
        })
        demo_data['ai_insights'] = enhanced.get('ai_insights', {})
    except Exception:
        demo_data['ai_insights'] = {'error': 'AI analysis unavailable'}

    # Ensure ai_insights is always a dict
    if not isinstance(demo_data.get('ai_insights'), dict):
        demo_data['ai_insights'] = {}

    # Add transparent risk quantification for async job payloads.
    analyzer = RiskAnalyzer()
    activity_analysis = {
        'risk_score': risk_score,
        'confidence': 75,
        'component_scores': {
            'process': risk_score,
            'network': risk_score,
            'system': risk_score,
        },
    }
    risk_quantification = analyzer.quantify_total_risk(activity_analysis, demo_data.get('ai_insights', {}))
    # Nest under ai_insights where frontend expects it
    demo_data['ai_insights']['risk_quantification'] = risk_quantification
    demo_data['activity_risk_score'] = risk_quantification['activity']['score']
    demo_data['llm_risk_score'] = risk_quantification['llm']['score']

    duration = (datetime.now() - start).total_seconds()
    demo_data['analysis_duration'] = round(duration, 2)
    return demo_data


def run_simulate_job() -> Dict[str, Any]:
    """
    Background job: run simulated analysis with a random scenario.
    """
    import random
    from services.rag_service import get_rag_service
    from services.risk_analyzer import RiskAnalyzer
    from utils.tree_builder import build_process_tree
    from app import get_demo_scenarios

    start = datetime.now()
    scenarios = get_demo_scenarios()
    scenario = random.choice(scenarios)
    process_tree = build_process_tree(scenario['processes'])
    risk_score = random.randint(*scenario['risk_range'])

    demo_data: Dict[str, Any] = {
        'summary': f"{scenario['name']} Analysis: {scenario['findings'][0]}",
        'key_findings': scenario['findings'],
        'risk_score': risk_score,
        'alerts': scenario['alerts'],
        'process_tree': process_tree,
        'generated_at': datetime.now().isoformat(timespec='seconds'),
        'status': 'completed',
    }

    try:
        rag_service = get_rag_service()
        enhanced = rag_service.analyze_with_context({
            'summary': demo_data['summary'],
            'risk_score': demo_data['risk_score'],
            'key_findings': demo_data['key_findings'],
            'process_tree': demo_data['process_tree'],
            'alerts': demo_data['alerts'],
        })
        demo_data['ai_insights'] = enhanced.get('ai_insights', {})
    except Exception:
        demo_data['ai_insights'] = {'error': 'AI analysis unavailable'}

    # Ensure ai_insights is always a dict
    if not isinstance(demo_data.get('ai_insights'), dict):
        demo_data['ai_insights'] = {}

    # Add transparent risk quantification for async simulated job payloads.
    analyzer = RiskAnalyzer()
    activity_analysis = {
        'risk_score': risk_score,
        'confidence': 75,
        'component_scores': {
            'process': risk_score,
            'network': risk_score,
            'system': risk_score,
        },
    }
    risk_quantification = analyzer.quantify_total_risk(activity_analysis, demo_data.get('ai_insights', {}))
    # Nest under ai_insights where frontend expects it
    demo_data['ai_insights']['risk_quantification'] = risk_quantification
    demo_data['activity_risk_score'] = risk_quantification['activity']['score']
    demo_data['llm_risk_score'] = risk_quantification['llm']['score']

    duration = (datetime.now() - start).total_seconds()
    demo_data['analysis_duration'] = round(duration, 2)
    return demo_data
