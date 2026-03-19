import json
import importlib.util
import logging
import os
import shutil
import time
import uuid
from datetime import datetime
from logging.handlers import RotatingFileHandler

from flask import current_app, g, has_request_context, request

from services.job_service import is_redis_available
from utils.database import check_database_connection


class JsonLogFormatter(logging.Formatter):
    """Format log records as single-line JSON for easier ingestion."""

    def format(self, record):
        payload = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
        }

        for field in (
            'event',
            'request_id',
            'method',
            'path',
            'status_code',
            'duration_ms',
            'remote_addr',
            'user_id',
        ):
            value = getattr(record, field, None)
            if value is not None:
                payload[field] = value

        if record.exc_info:
            payload['exception'] = self.formatException(record.exc_info)

        return json.dumps(payload, default=str)


class RequestContextFilter(logging.Filter):
    """Attach request metadata to log records when a request context exists."""

    def filter(self, record):
        if has_request_context():
            record.request_id = getattr(g, 'request_id', None)
            record.method = request.method
            record.path = request.path
            record.remote_addr = request.headers.get('X-Forwarded-For', request.remote_addr)
            record.user_id = getattr(g, 'user_id', None)
        return True


def configure_logging(app):
    """Configure application and request logging."""
    log_dir = app.config.get('LOG_DIR', 'logs')
    os.makedirs(log_dir, exist_ok=True)

    formatter = JsonLogFormatter()
    context_filter = RequestContextFilter()

    file_handler = RotatingFileHandler(
        os.path.join(log_dir, 'vollite.log'),
        maxBytes=app.config.get('LOG_MAX_BYTES', 1024 * 1024),
        backupCount=app.config.get('LOG_BACKUP_COUNT', 3),
        encoding='utf-8',
    )
    file_handler.setLevel(getattr(logging, app.config.get('LOG_LEVEL', 'INFO').upper(), logging.INFO))
    file_handler.setFormatter(formatter)
    file_handler.addFilter(context_filter)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(getattr(logging, app.config.get('LOG_LEVEL', 'INFO').upper(), logging.INFO))
    stream_handler.setFormatter(formatter)
    stream_handler.addFilter(context_filter)

    app.logger.handlers.clear()
    app.logger.setLevel(getattr(logging, app.config.get('LOG_LEVEL', 'INFO').upper(), logging.INFO))
    app.logger.addHandler(file_handler)
    app.logger.addHandler(stream_handler)
    app.logger.propagate = False

    werkzeug_logger = logging.getLogger('werkzeug')
    werkzeug_logger.handlers.clear()
    werkzeug_logger.setLevel(app.logger.level)
    werkzeug_logger.addHandler(file_handler)
    werkzeug_logger.addHandler(stream_handler)
    werkzeug_logger.propagate = False


def begin_request_tracking():
    """Initialize per-request timing and correlation metadata."""
    g.request_id = request.headers.get('X-Request-ID') or str(uuid.uuid4())
    g.request_started_at = time.perf_counter()
    g.request_started_utc = datetime.utcnow()


def finalize_response(response):
    """Attach monitoring headers and emit a request completion log."""
    started_at = getattr(g, 'request_started_at', None)
    duration_ms = round((time.perf_counter() - started_at) * 1000, 2) if started_at else None

    response.headers['X-Request-ID'] = getattr(g, 'request_id', 'unknown')
    if duration_ms is not None:
        response.headers['X-Response-Time-ms'] = str(duration_ms)

    current_app.logger.info(
        'request_complete',
        extra={
            'event': 'request_complete',
            'status_code': response.status_code,
            'duration_ms': duration_ms,
        },
    )
    return response


def build_rag_health():
    """Return dependency and configuration status for RAG services."""
    has_groq_key = bool(os.getenv('GROQ_API_KEY'))
    langchain_available = importlib.util.find_spec('langchain_text_splitters') is not None
    groq_available = importlib.util.find_spec('langchain_groq') is not None
    chromadb_available = importlib.util.find_spec('chromadb') is not None

    return {
        'langchain_available': langchain_available,
        'groq_available': groq_available,
        'chromadb_available': chromadb_available,
        'groq_api_key_configured': has_groq_key,
        'status': 'ready' if langchain_available and groq_available and chromadb_available and has_groq_key else 'degraded',
    }


def build_disk_health(path):
    """Return disk usage details for the filesystem containing the upload path."""
    target_path = os.path.abspath(path or '.')
    os.makedirs(target_path, exist_ok=True)
    usage = shutil.disk_usage(target_path)
    return {
        'path': target_path,
        'total_bytes': usage.total,
        'used_bytes': usage.used,
        'free_bytes': usage.free,
    }


def build_health_snapshot(app):
    """Build a richer health response for API monitoring."""
    started_at = app.config.get('APP_START_TIME')
    uptime_seconds = None
    if started_at is not None:
        uptime_seconds = round((datetime.utcnow() - started_at).total_seconds(), 2)

    db_status = check_database_connection()
    redis_available = is_redis_available()
    rag_status = build_rag_health()
    disk_status = build_disk_health(app.config.get('UPLOAD_FOLDER', 'uploads'))

    overall_status = 'healthy'
    if db_status['status'] != 'connected':
        overall_status = 'degraded'
    elif not redis_available or rag_status['status'] != 'ready':
        overall_status = 'degraded'

    request_started = getattr(g, 'request_started_utc', None)

    return {
        'status': overall_status,
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.1.0-monitoring',
        'request_id': getattr(g, 'request_id', None),
        'request_started_at': request_started.isoformat() if request_started else None,
        'uptime_seconds': uptime_seconds,
        'database': db_status,
        'redis': {
            'status': 'connected' if redis_available else 'unavailable',
        },
        'rag': rag_status,
        'disk': disk_status,
        'logging': {
            'level': app.config.get('LOG_LEVEL', 'INFO'),
            'directory': app.config.get('LOG_DIR', 'logs'),
        },
    }