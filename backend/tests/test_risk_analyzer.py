"""
Unit tests for services/risk_analyzer.py

Tests the RiskAnalyzer scoring engine in isolation — no Flask app or DB needed.
"""

from services.risk_analyzer import RiskAnalyzer


class TestRiskAnalyzerEmpty:
    """When all data is empty the score should be zero / minimal."""

    def test_empty_data_returns_minimal(self):
        analyzer = RiskAnalyzer()
        result = analyzer.analyze_risk({}, {}, {})

        assert result['risk_score'] == 0
        assert result['risk_level'] == 'Minimal'
        assert result['risk_factors'] == []
        assert isinstance(result['recommendations'], list)

    def test_empty_processes_list(self):
        analyzer = RiskAnalyzer()
        result = analyzer.analyze_risk({'processes': []}, {'connections': []}, {})
        assert result['risk_score'] == 0


class TestProcessAnalysis:
    """Process-based risk detection."""

    def _make_proc(self, name, path='', cmdline='', pid=100, ppid=1):
        return {'name': name, 'path': path, 'cmdline': cmdline,
                'pid': pid, 'ppid': ppid}

    def test_lolbin_detected(self):
        """LOLBins like rundll32.exe should raise the score."""
        proc = self._make_proc('rundll32.exe', path='c:\\windows\\system32\\rundll32.exe')
        analyzer = RiskAnalyzer()
        result = analyzer.analyze_risk({'processes': [proc]}, {}, {})

        assert result['risk_score'] > 0
        categories = [f['category'] for f in result['risk_factors']]
        assert 'LOLBin Usage' in categories

    def test_encoded_powershell(self):
        """PowerShell with -EncodedCommand should flag Critical."""
        proc = self._make_proc('powershell.exe',
                               cmdline='powershell.exe -EncodedCommand ZABpAHIAIAA=')
        analyzer = RiskAnalyzer()
        result = analyzer.analyze_risk({'processes': [proc]}, {}, {})

        assert result['risk_score'] > 0
        severities = [f['severity'] for f in result['risk_factors']]
        assert 'Critical' in severities

    def test_suspicious_parent_child(self):
        """notepad.exe spawning powershell.exe should flag Process Anomaly."""
        parent = self._make_proc('notepad.exe', pid=10, ppid=1)
        child = self._make_proc('powershell.exe', pid=20, ppid=10)
        analyzer = RiskAnalyzer()
        result = analyzer.analyze_risk({'processes': [parent, child]}, {}, {})

        categories = [f['category'] for f in result['risk_factors']]
        assert 'Process Anomaly' in categories

    def test_suspicious_path(self):
        """Processes running from temp dir should flag Suspicious Location."""
        proc = self._make_proc('malware.exe', path='c:\\temp\\malware.exe')
        analyzer = RiskAnalyzer()
        result = analyzer.analyze_risk({'processes': [proc]}, {}, {})

        categories = [f['category'] for f in result['risk_factors']]
        assert 'Suspicious Location' in categories

    def test_unsigned_binary(self):
        proc = self._make_proc('svchost.exe')
        proc['signature_status'] = 'unsigned'
        analyzer = RiskAnalyzer()
        result = analyzer.analyze_risk({'processes': [proc]}, {}, {})

        categories = [f['category'] for f in result['risk_factors']]
        assert 'Code Signing' in categories

    def test_clean_process_no_flags(self):
        """A normal process should not generate risk factors."""
        proc = self._make_proc('explorer.exe',
                               path='c:\\windows\\explorer.exe', pid=5, ppid=1)
        analyzer = RiskAnalyzer()
        result = analyzer.analyze_risk({'processes': [proc]}, {}, {})
        assert result['risk_factors'] == []


class TestNetworkAnalysis:

    def _conn(self, remote, protocol='TCP'):
        return {'remote': remote, 'protocol': protocol}

    def test_suspicious_port(self):
        conn = self._conn('10.0.0.1:4444')
        analyzer = RiskAnalyzer()
        result = analyzer.analyze_risk({}, {'connections': [conn]}, {})

        assert result['risk_score'] > 0
        categories = [f['category'] for f in result['risk_factors']]
        assert 'Network Anomaly' in categories

    def test_non_standard_web_port(self):
        conn = self._conn('10.0.0.1:8080')
        analyzer = RiskAnalyzer()
        result = analyzer.analyze_risk({}, {'connections': [conn]}, {})
        # 8080 is both in _suspicious_ports and non-standard web ports set;
        # at least one network-related factor should appear.
        assert any('Network' in f['category'] for f in result['risk_factors'])

    def test_clean_connection(self):
        conn = self._conn('10.0.0.1:443')
        analyzer = RiskAnalyzer()
        result = analyzer.analyze_risk({}, {'connections': [conn]}, {})
        assert result['risk_score'] == 0

    def test_malformed_remote_ignored(self):
        """Connections with no port should not crash."""
        conn = {'remote': 'bad-data', 'protocol': 'TCP'}
        analyzer = RiskAnalyzer()
        result = analyzer.analyze_risk({}, {'connections': [conn]}, {})
        assert result['risk_score'] == 0


class TestSystemAnalysis:

    def test_registry_persistence(self):
        system_info = {
            'registry': [
                {'key': 'HKLM\\Software\\Microsoft\\Windows\\CurrentVersion\\Run',
                 'value': 'malware.exe'}
            ]
        }
        analyzer = RiskAnalyzer()
        result = analyzer.analyze_risk({}, {}, system_info)

        categories = [f['category'] for f in result['risk_factors']]
        assert 'Persistence' in categories

    def test_executable_in_temp(self):
        system_info = {
            'files': [
                {'path': 'C:\\Users\\Public\\Temp\\evil.exe', 'executable': True}
            ]
        }
        analyzer = RiskAnalyzer()
        result = analyzer.analyze_risk({}, {}, system_info)

        categories = [f['category'] for f in result['risk_factors']]
        assert 'File System' in categories


class TestRiskLevelMapping:
    """Verify _get_risk_level thresholds."""

    def test_risk_levels(self):
        analyzer = RiskAnalyzer()

        analyzer.total_score = 0
        assert analyzer._get_risk_level() == 'Minimal'

        analyzer.total_score = 25
        assert analyzer._get_risk_level() == 'Low'

        analyzer.total_score = 45
        assert analyzer._get_risk_level() == 'Medium'

        analyzer.total_score = 65
        assert analyzer._get_risk_level() == 'High'

        analyzer.total_score = 85
        assert analyzer._get_risk_level() == 'Critical'


class TestScoreCapping:

    def test_score_capped_at_100(self):
        """Even with many indicators the score must not exceed 100."""
        procs = [
            {'name': 'rundll32.exe', 'path': 'c:\\temp\\rundll32.exe',
             'cmdline': '', 'pid': i, 'ppid': 1, 'signature_status': 'unsigned'}
            for i in range(10, 50)
        ]
        analyzer = RiskAnalyzer()
        result = analyzer.analyze_risk({'processes': procs}, {}, {})
        assert result['risk_score'] <= 100


class TestCaching:

    def test_cache_hit(self):
        """Second call with identical data should return cached result."""
        data = {'processes': [{'name': 'svchost.exe', 'pid': 1, 'ppid': 0,
                               'path': '', 'cmdline': ''}]}
        analyzer = RiskAnalyzer()
        r1 = analyzer.analyze_risk(data, {}, {})
        r2 = analyzer.analyze_risk(data, {}, {})
        assert r2['performance']['cached'] is True
        assert r1['risk_score'] == r2['risk_score']

    def test_clear_cache(self):
        analyzer = RiskAnalyzer()
        analyzer.analyze_risk({'processes': []}, {}, {})
        analyzer.clear_cache()
        assert analyzer.get_cache_stats()['cache_size'] == 0


class TestRecommendations:

    def test_clean_system_recommendations(self):
        analyzer = RiskAnalyzer()
        result = analyzer.analyze_risk({}, {}, {})
        assert any('clean' in r.lower() or 'minimal' in r.lower()
                    for r in result['recommendations'])

    def test_recommendations_for_lolbin(self):
        proc = {'name': 'certutil.exe', 'path': '', 'cmdline': '',
                'pid': 10, 'ppid': 1}
        analyzer = RiskAnalyzer()
        result = analyzer.analyze_risk({'processes': [proc]}, {}, {})
        assert any('lolbin' in r.lower() or 'living' in r.lower() or 'whitelist' in r.lower()
                    for r in result['recommendations'])
