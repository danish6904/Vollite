"""
Tests for background job service and job status API.
Tests cover: sync fallback, job service helpers, job status endpoint.
"""

import json
from unittest.mock import patch, MagicMock
from services.job_service import (
    get_redis_connection,
    is_redis_available,
    get_job_status,
    enqueue_job,
    run_analysis_job,
    run_simulate_job,
)


# ── Redis connection tests ──────────────────────────────────────────────────

class TestRedisConnection:
    """Test Redis connection handling"""

    def test_get_redis_connection_no_server(self):
        """When Redis is not running, returns None instead of crashing"""
        with patch.dict('os.environ', {'REDIS_HOST': 'localhost', 'REDIS_PORT': '59999'}):
            conn = get_redis_connection()
            assert conn is None

    def test_is_redis_available_no_server(self):
        """is_redis_available returns False without Redis"""
        with patch('services.job_service.get_redis_connection', return_value=None):
            assert is_redis_available() is False

    def test_enqueue_job_no_redis(self):
        """enqueue_job returns None when Redis is unreachable"""
        with patch('services.job_service.get_redis_connection', return_value=None):
            result = enqueue_job(lambda: None)
            assert result is None


# ── Job status tests ────────────────────────────────────────────────────────

class TestGetJobStatus:
    """Test job status querying"""

    def test_status_redis_unavailable(self):
        """Returns error when Redis is down"""
        with patch('services.job_service.get_redis_connection', return_value=None):
            result = get_job_status('fake-id')
            assert result['status'] == 'error'
            assert 'Redis unavailable' in result['error']

    def test_status_job_not_found(self):
        """Returns not_found for unknown job"""
        mock_conn = MagicMock()
        mock_conn.hgetall.return_value = {}
        with patch('services.job_service.get_redis_connection', return_value=mock_conn):
            result = get_job_status('nonexistent')
            assert result['status'] == 'not_found'

    def test_status_job_finished(self):
        """Returns result when job is finished"""
        finished_data = {
            'status': 'finished',
            'result': json.dumps({'summary': 'done', 'status': 'completed'}),
            'error': '',
        }
        mock_conn = MagicMock()
        mock_conn.hgetall.return_value = finished_data
        with patch('services.job_service.get_redis_connection', return_value=mock_conn):
            result = get_job_status('some-id')
            assert result['status'] == 'finished'
            assert result['result']['summary'] == 'done'

    def test_status_job_failed(self):
        """Returns error when job failed"""
        failed_data = {
            'status': 'failed',
            'result': '',
            'error': 'RuntimeError: boom',
        }
        mock_conn = MagicMock()
        mock_conn.hgetall.return_value = failed_data
        with patch('services.job_service.get_redis_connection', return_value=mock_conn):
            result = get_job_status('fail-id')
            assert result['status'] == 'failed'
            assert 'boom' in result['error']

    def test_status_job_queued(self):
        """Returns queued status for pending job"""
        queued_data = {
            'status': 'queued',
            'result': '',
            'error': '',
        }
        mock_conn = MagicMock()
        mock_conn.hgetall.return_value = queued_data
        with patch('services.job_service.get_redis_connection', return_value=mock_conn):
            result = get_job_status('pending-id')
            assert result['status'] == 'queued'
            assert 'result' not in result


# ── Job status API endpoint tests ───────────────────────────────────────────

class TestJobStatusEndpoint:
    """Test /api/jobs/status/<job_id> endpoint"""

    def test_job_status_not_found(self, client):
        """404 when job doesn't exist"""
        mock_conn = MagicMock()
        mock_conn.hgetall.return_value = {}
        with patch('services.job_service.get_redis_connection', return_value=mock_conn):
            res = client.get('/api/jobs/status/nonexistent')
            assert res.status_code == 404

    def test_job_status_redis_down(self, client):
        """503 when Redis is unreachable"""
        with patch('services.job_service.get_redis_connection', return_value=None):
            res = client.get('/api/jobs/status/some-id')
            assert res.status_code == 503

    def test_jobs_health_no_redis(self, client):
        """Health endpoint reports disabled when Redis is down"""
        with patch('api.jobs.is_redis_available', return_value=False):
            res = client.get('/api/jobs/health')
            assert res.status_code == 503
            data = res.get_json()
            assert data['redis_available'] is False


# ── Sync fallback tests ─────────────────────────────────────────────────────

class TestSyncFallback:
    """Test that analysis works synchronously when Redis is unavailable"""

    def test_simulate_sync_fallback(self, client):
        """Simulate analysis falls back to sync when no Redis"""
        with patch('services.job_service.get_redis_connection', return_value=None):
            res = client.post('/api/analyze',
                              json={'simulate': True},
                              content_type='application/json')
            assert res.status_code == 200
            data = res.get_json()
            assert data['status'] == 'completed'
            assert 'summary' in data
            assert 'risk_score' in data

    def test_simulate_queued_with_redis(self, client):
        """Simulate analysis returns 202 when Redis is available"""
        mock_conn = MagicMock()
        mock_conn.ping.return_value = True
        mock_conn.hset.return_value = True
        mock_conn.expire.return_value = True

        with patch('services.job_service.get_redis_connection', return_value=mock_conn):
            res = client.post('/api/analyze',
                              json={'simulate': True},
                              content_type='application/json')
            assert res.status_code == 202
            data = res.get_json()
            assert data['status'] == 'queued'
            assert 'job_id' in data


# ── Job function unit tests ────────────────────────────────────────────────

class TestJobFunctions:
    """Test the actual job functions that run in workers"""

    def test_run_simulate_job(self, app):
        """run_simulate_job returns complete analysis data"""
        with app.app_context():
            with patch('services.rag_service.get_rag_service') as mock_rag:
                mock_svc = MagicMock()
                mock_svc.analyze_with_context.return_value = {
                    'ai_insights': {'summary': 'test insight'}
                }
                mock_rag.return_value = mock_svc

                result = run_simulate_job()
                assert result['status'] == 'completed'
                assert 'summary' in result
                assert 'risk_score' in result
                assert 'process_tree' in result
                assert result['ai_insights']['summary'] == 'test insight'
                assert 'risk_quantification' in result
                assert 'activity_risk_score' in result
                assert 'llm_risk_score' in result

    def test_run_analysis_job(self, app):
        """run_analysis_job returns complete analysis data"""
        with app.app_context():
            with patch('services.rag_service.get_rag_service') as mock_rag:
                mock_svc = MagicMock()
                mock_svc.analyze_with_context.return_value = {
                    'ai_insights': {'summary': 'analyzed'}
                }
                mock_rag.return_value = mock_svc

                scenario_data = {
                    'name': 'Test Scenario',
                    'processes': [
                        {'pid': 4, 'name': 'System', 'ppid': 0},
                    ],
                    'findings': ['Test finding'],
                    'alerts': [],
                    'risk_score': 42,
                }

                result = run_analysis_job(
                    'test.dmp',
                    {'sha256': 'abc', 'file_size': 100},
                    scenario_data,
                )
                assert result['status'] == 'completed'
                assert result['risk_score'] == 42
                assert 'test.dmp' in result['summary']
                assert result['ai_insights']['summary'] == 'analyzed'
                assert 'risk_quantification' in result
                assert 'activity_risk_score' in result
                assert 'llm_risk_score' in result

    def test_run_analysis_job_rag_failure(self, app):
        """Job still completes even when RAG fails"""
        with app.app_context():
            with patch('services.rag_service.get_rag_service', side_effect=Exception('boom')):
                scenario_data = {
                    'name': 'Test',
                    'processes': [],
                    'findings': ['f'],
                    'alerts': [],
                    'risk_score': 10,
                }

                result = run_analysis_job(
                    'test.dmp', {}, scenario_data,
                )
                assert result['status'] == 'completed'
                assert result['ai_insights']['error'] == 'AI analysis unavailable'
                assert 'risk_quantification' in result
                assert 'activity_risk_score' in result
                assert 'llm_risk_score' in result
