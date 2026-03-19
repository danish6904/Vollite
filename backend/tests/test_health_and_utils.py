"""
Integration tests for health-check and system-info endpoints,
plus the process-tree builder utility.
"""

from utils.tree_builder import build_process_tree


class TestHealthEndpoint:

    def test_health_returns_200(self, client):
        resp = client.get('/api/health')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['status'] in ['healthy', 'degraded']
        assert 'timestamp' in data
        assert 'database' in data
        assert 'request_id' in data
        assert 'redis' in data
        assert 'rag' in data
        assert 'disk' in data

    def test_health_response_headers(self, client):
        resp = client.get('/api/health')
        assert resp.status_code == 200
        assert 'X-Request-ID' in resp.headers
        assert 'X-Response-Time-ms' in resp.headers

    def test_system_info(self, client):
        resp = client.get('/api/system/info')
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'volatility' in data
        assert 'database' in data
        assert 'redis' in data
        assert 'rag' in data
        assert 'disk' in data


class TestFrontendRoutes:

    def test_home_page(self, client):
        resp = client.get('/')
        assert resp.status_code == 200

    def test_about_page(self, client):
        resp = client.get('/about')
        assert resp.status_code == 200

    def test_contact_page(self, client):
        resp = client.get('/contact')
        assert resp.status_code == 200

    def test_dashboard_page(self, client):
        resp = client.get('/dashboard')
        assert resp.status_code == 200


class TestProcessTreeBuilder:

    def test_empty_processes(self):
        tree = build_process_tree([])
        assert tree['name'] == 'No Processes Found'

    def test_single_process(self):
        procs = [{'name': 'System', 'pid': 4, 'ppid': 0, 'cmdline': ''}]
        tree = build_process_tree(procs)
        assert tree['name'] == 'System'

    def test_parent_child(self):
        procs = [
            {'name': 'System', 'pid': 4, 'ppid': 0, 'cmdline': ''},
            {'name': 'svchost.exe', 'pid': 100, 'ppid': 4, 'cmdline': ''}
        ]
        tree = build_process_tree(procs)
        assert tree['name'] == 'System'
        assert any(c['name'] == 'svchost.exe' for c in tree['children'])

    def test_orphan_processes(self):
        procs = [
            {'name': 'A', 'pid': 1, 'ppid': 999, 'cmdline': ''},
            {'name': 'B', 'pid': 2, 'ppid': 888, 'cmdline': ''}
        ]
        tree = build_process_tree(procs)
        # Both orphans → virtual root with two children
        assert tree['name'] == 'System Root'
        assert len(tree['children']) == 2

    def test_malicious_process_risk(self):
        procs = [{'name': 'mimikatz.exe', 'pid': 10, 'ppid': 0, 'cmdline': ''}]
        tree = build_process_tree(procs)
        assert tree['risk'] == 'Critical'
