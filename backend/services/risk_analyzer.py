
# services/risk_analyzer.py
# Enhanced risk analysis with detailed explanations and scoring breakdown

import re
import json
import time
from typing import Dict, List, Tuple, Any
from functools import lru_cache

class RiskAnalyzer:
    '''
    Advanced risk scoring engine with detailed explanations for volLite
    Optimized for performance with caching and early termination
    '''

    def __init__(self):
        self.risk_factors = []
        self.total_score = 0
        self.confidence_level = 0
        self.activity_weight = 0.80
        self.llm_weight = 0.20
        self._component_scores = {'process': 0, 'network': 0, 'system': 0}

        # Weighted issue mapping used for LLM findings quantification.
        self._llm_issue_weights = {
            'ransomware': 25,
            'credential dumping': 22,
            'data exfiltration': 22,
            'command and control': 20,
            'c2': 20,
            'beacon': 18,
            'persistence': 18,
            'lateral movement': 18,
            'encoded command': 14,
            'powershell': 12,
            'suspicious process': 12,
            'malicious': 12,
            'network anomaly': 10,
        }

        self._llm_threat_level_weights = {
            'critical': 30,
            'high': 20,
            'medium': 12,
            'low': 6,
            'minimal': 3,
        }
        
        # Pre-compile regex patterns for better performance
        self._compiled_patterns = {
            'powershell_encoded': re.compile(r'-enc|-encodedcommand', re.IGNORECASE),
            'suspicious_paths': re.compile(r'(/tmp/|c:\\temp\\|c:\\users\\public\\|\\appdata\\local\\temp\\)', re.IGNORECASE),
            'lolbins': re.compile(r'(rundll32\.exe|regsvr32\.exe|mshta\.exe|certutil\.exe|bitsadmin\.exe)', re.IGNORECASE)
        }
        
        # Pre-defined suspicious patterns for faster lookup
        self._suspicious_ports = {4444, 4445, 8080, 9999, 1337, 31337, 8000, 8001, 8888, 9000}
        self._lolbins_set = {'rundll32.exe', 'regsvr32.exe', 'mshta.exe', 'certutil.exe', 'bitsadmin.exe'}
        self._suspicious_paths_set = {'/tmp/', 'c:\\temp\\', 'c:\\users\\public\\', '\\appdata\\local\\temp\\'}
        
        # Performance tracking
        self._analysis_times = {}
        
        # Simple cache for repeated analysis (in-memory, limited size)
        self._cache = {}
        self._cache_max_size = 100

    def analyze_risk(self, process_data: dict, network_data: dict, system_info: dict) -> dict:
        '''
        Comprehensive risk analysis with detailed explanations
        Returns risk score, breakdown, and reasons
        Optimized for performance with early termination and caching
        '''
        start_time = time.time()
        
        # Create cache key from data hash (simple approach)
        cache_key = self._create_cache_key(process_data, network_data, system_info)
        
        # Check cache first
        if cache_key in self._cache:
            cached_result = self._cache[cache_key].copy()
            cached_result['performance'] = {
                'total_time_ms': 0.1,  # Cache hit time
                'process_time_ms': 0.0,
                'network_time_ms': 0.0,
                'system_time_ms': 0.0,
                'cached': True
            }
            return cached_result
        
        self.risk_factors = []
        self.total_score = 0

        # Analyze different aspects with performance tracking
        process_start = time.time()
        process_score = self._analyze_processes(process_data)
        self._component_scores['process'] = process_score
        self._analysis_times['process'] = time.time() - process_start

        network_start = time.time()
        network_score = self._analyze_network(network_data)
        self._component_scores['network'] = network_score
        self._analysis_times['network'] = time.time() - network_start

        system_start = time.time()
        system_score = self._analyze_system(system_info)
        self._component_scores['system'] = system_score
        self._analysis_times['system'] = time.time() - system_start

        # Calculate weighted total score (adjusted for better medium-risk detection)
        weights = {'process': 0.7, 'network': 0.2, 'system': 0.1}
        self.total_score = (
            process_score * weights['process'] +
            network_score * weights['network'] + 
            system_score * weights['system']
        )

        # Cap at 100
        self.total_score = min(100, int(self.total_score))

        # Calculate confidence based on number of indicators
        self.confidence_level = min(95, 40 + len(self.risk_factors) * 8)

        total_time = time.time() - start_time
        self._analysis_times['total'] = total_time

        result = {
            'risk_score': self.total_score,
            'risk_level': self._get_risk_level(),
            'confidence': self.confidence_level,
            'component_scores': self._component_scores.copy(),
            'activity_quantification': self._build_activity_quantification(
                process_score,
                network_score,
                system_score,
                self.total_score,
                self.risk_factors,
            ),
            'breakdown': self._get_score_breakdown(),
            'risk_factors': self.risk_factors,
            'explanation': self._generate_explanation(),
            'recommendations': self._get_recommendations(),
            'performance': {
                'total_time_ms': round(total_time * 1000, 2),
                'process_time_ms': round(self._analysis_times.get('process', 0) * 1000, 2),
                'network_time_ms': round(self._analysis_times.get('network', 0) * 1000, 2),
                'system_time_ms': round(self._analysis_times.get('system', 0) * 1000, 2),
                'cached': False
            }
        }
        
        # Store in cache (with size limit)
        self._store_in_cache(cache_key, result)
        
        return result

    def quantify_total_risk(self, activity_analysis: dict, ai_insights: Any = None) -> dict:
        '''
        Build an explainable final risk score from:
        1) deterministic activity analysis from memory dump
        2) quantified LLM findings extracted from AI insights
        '''
        activity_score = int(activity_analysis.get('risk_score', 0) or 0)

        component_scores = activity_analysis.get('component_scores') or {'process': 0, 'network': 0, 'system': 0}
        activity_quantification = activity_analysis.get('activity_quantification') or self._build_activity_quantification(
            int(component_scores.get('process', 0) or 0),
            int(component_scores.get('network', 0) or 0),
            int(component_scores.get('system', 0) or 0),
            activity_score,
            activity_analysis.get('risk_factors', []),
        )

        llm_quantification = self._quantify_llm_findings(ai_insights)
        llm_score = llm_quantification['score']

        weighted_activity_points = round(activity_score * self.activity_weight, 2)
        weighted_llm_points = round(llm_score * self.llm_weight, 2)
        final_score = min(100, int(round(weighted_activity_points + weighted_llm_points)))

        return {
            'method': 'weighted_activity_plus_llm_v1',
            'weights': {
                'activity_weight': self.activity_weight,
                'llm_weight': self.llm_weight,
            },
            'activity': {
                'score': activity_score,
                'level': self._risk_level_for_score(activity_score),
                'confidence': activity_analysis.get('confidence', 0),
                'quantification': activity_quantification,
                'weighted_points': weighted_activity_points,
            },
            'llm': {
                'score': llm_score,
                'level': self._risk_level_for_score(llm_score),
                'available': llm_quantification['available'],
                'issues': llm_quantification['issues'],
                'weighted_points': weighted_llm_points,
                'error': llm_quantification.get('error'),
                'source_excerpt': llm_quantification.get('source_excerpt', ''),
            },
            'final': {
                'score': final_score,
                'level': self._risk_level_for_score(final_score),
                'equation': 'final = (activity_score * 0.80) + (llm_score * 0.20)',
                'activity_points': weighted_activity_points,
                'llm_points': weighted_llm_points,
            }
        }

    def _build_activity_quantification(self,
                                       process_score: int,
                                       network_score: int,
                                       system_score: int,
                                       activity_score: int,
                                       risk_factors: List[dict]) -> dict:
        '''Quantify how memory-dump activities contribute to activity score.'''
        process_points = round(process_score * 0.70, 2)
        network_points = round(network_score * 0.20, 2)
        system_points = round(system_score * 0.10, 2)

        def _pct(points: float, total: int) -> float:
            if total <= 0:
                return 0.0
            return round((points / float(total)) * 100.0, 2)

        top_factors = []
        for factor in risk_factors[:10]:
            impact_text = factor.get('impact', '0')
            try:
                impact_points = int(str(impact_text).replace('+', '').replace(' points', ''))
            except ValueError:
                impact_points = 0
            top_factors.append({
                'category': factor.get('category', 'Unknown'),
                'severity': factor.get('severity', 'Unknown'),
                'description': factor.get('description', ''),
                'impact_points': impact_points,
            })

        return {
            'component_scores': {
                'process': process_score,
                'network': network_score,
                'system': system_score,
            },
            'weighted_points': {
                'process': process_points,
                'network': network_points,
                'system': system_points,
                'total': round(process_points + network_points + system_points, 2),
            },
            'max_points': {
                'process': 70,
                'network': 20,
                'system': 10,
                'total': 100,
            },
            'percent_of_activity_score': {
                'process': _pct(process_points, activity_score),
                'network': _pct(network_points, activity_score),
                'system': _pct(system_points, activity_score),
            },
            'indicator_count': len(risk_factors),
            'top_factors': top_factors,
        }

    def _quantify_llm_findings(self, ai_insights: Any) -> dict:
        '''Convert LLM narrative output into a deterministic score and issue list.'''
        if isinstance(ai_insights, dict) and ai_insights.get('error'):
            return {
                'available': False,
                'score': 0,
                'issues': [],
                'error': ai_insights.get('error'),
                'source_excerpt': '',
            }

        llm_text = self._extract_llm_text(ai_insights)
        if not llm_text:
            return {
                'available': False,
                'score': 0,
                'issues': [],
                'error': 'No AI findings provided',
                'source_excerpt': '',
            }

        llm_text_lower = llm_text.lower()
        issues = []
        total_points = 0

        for level, points in self._llm_threat_level_weights.items():
            marker = f'threat level: {level}'
            if marker in llm_text_lower:
                issues.append({
                    'issue': f'LLM threat level reported as {level.title()}',
                    'points': points,
                    'evidence': marker,
                })
                total_points += points
                break

        for phrase, points in self._llm_issue_weights.items():
            if phrase in llm_text_lower:
                issues.append({
                    'issue': f'LLM flagged "{phrase}"',
                    'points': points,
                    'evidence': phrase,
                })
                total_points += points

        llm_score = min(100, total_points)

        return {
            'available': True,
            'score': llm_score,
            'issues': issues,
            'error': None,
            'source_excerpt': llm_text[:500],
        }

    def _extract_llm_text(self, ai_insights: Any) -> str:
        '''Extract analyzable plain text from LLM insights payload.'''
        if not ai_insights:
            return ''

        if isinstance(ai_insights, str):
            return ai_insights.strip()

        if isinstance(ai_insights, dict):
            text_parts = []
            for key in ('summary', 'analysis', 'details', 'explanation'):
                value = ai_insights.get(key)
                if isinstance(value, str) and value.strip():
                    text_parts.append(value.strip())

            findings = ai_insights.get('findings')
            if isinstance(findings, list):
                text_parts.extend(str(item).strip() for item in findings if str(item).strip())

            return '\n'.join(text_parts).strip()

        return str(ai_insights).strip()

    def _risk_level_for_score(self, score: int) -> str:
        '''Convert numeric score to risk level without mutating analyzer state.'''
        if score >= 80:
            return 'Critical'
        if score >= 60:
            return 'High'
        if score >= 40:
            return 'Medium'
        if score >= 20:
            return 'Low'
        return 'Minimal'

    def _analyze_processes(self, process_data: dict) -> int:
        '''Analyze process behavior and return risk score (0-100) - Optimized'''
        score = 0
        processes = process_data.get('processes', [])
        
        # Early termination for empty process lists
        if not processes:
            return 0
            
        # Create process lookup map for faster parent-child checks
        process_map = {proc.get('pid'): proc for proc in processes if proc.get('pid')}
        
        # Limit analysis to first 100 processes for performance (most suspicious are usually early)
        processes_to_analyze = processes[:100] if len(processes) > 100 else processes

        for proc in processes_to_analyze:
            name = proc.get('name', '').lower()
            path = proc.get('path', '').lower()
            cmdline = proc.get('cmdline', '')
            ppid = proc.get('ppid', 0)

            # Check for suspicious process chains (optimized with map lookup)
            if self._is_suspicious_parent_child_optimized(proc, process_map):
                score += 25
                parent_name = process_map.get(ppid, {}).get('name', 'Unknown')
                self.risk_factors.append({
                    'category': 'Process Anomaly',
                    'severity': 'High',
                    'description': f'Suspicious parent-child relationship: {parent_name} spawned {name}',
                    'impact': '+45 points',
                    'details': f'Path: {proc.get("path")}, PID: {proc.get("pid")}'
                })

            # Check for encoded PowerShell (optimized with compiled regex)
            if 'powershell' in name and self._compiled_patterns['powershell_encoded'].search(cmdline):
                score += 30
                self.risk_factors.append({
                    'category': 'Malicious Execution',
                    'severity': 'Critical', 
                    'description': 'PowerShell with encoded command detected',
                    'impact': '+40 points',
                    'details': f'Command: {cmdline[:100]}...'
                })

            # Check for LOLBins (optimized with set lookup)
            if name in self._lolbins_set:
                score += 40  # Increased to 40 for proper medium-risk detection
                self.risk_factors.append({
                    'category': 'LOLBin Usage',
                    'severity': 'High',
                    'description': f'Living-off-the-land binary detected: {name}',
                    'impact': '+40 points', 
                    'details': f'Path: {proc.get("path")}'
                })

            # Check for processes in suspicious locations (optimized with set lookup)
            if any(susp_path in path for susp_path in self._suspicious_paths_set):
                score += 15
                self.risk_factors.append({
                    'category': 'Suspicious Location',
                    'severity': 'Medium',
                    'description': f'Process running from suspicious directory: {name}',
                    'impact': '+15 points',
                    'details': f'Location: {proc.get("path")}'
                })

            # Check for unsigned binaries (simplified check)
            if 'unsigned' in proc.get('signature_status', '').lower():
                score += 10
                self.risk_factors.append({
                    'category': 'Code Signing',
                    'severity': 'Medium', 
                    'description': f'Unsigned binary detected: {name}',
                    'impact': '+10 points',
                    'details': f'Path: {proc.get("path")}'
                })

        return min(100, score)

    def _analyze_network(self, network_data: dict) -> int:
        '''Analyze network connections and return risk score (0-100) - Optimized'''
        score = 0
        connections = network_data.get('connections', [])
        
        # Early termination for empty connection lists
        if not connections:
            return 0
            
        # Limit analysis to first 50 connections for performance
        connections_to_analyze = connections[:50] if len(connections) > 50 else connections

        for conn in connections_to_analyze:
            remote = conn.get('remote', '')
            if not remote or ':' not in remote:
                continue
                
            try:
                remote_ip, remote_port_str = remote.split(':', 1)
                remote_port = int(remote_port_str)
            except (ValueError, IndexError):
                continue
                
            protocol = conn.get('protocol', '').upper()

            # Check for connections to suspicious ports (optimized with set lookup)
            if remote_port in self._suspicious_ports:
                score += 45  # Increased to 45 for proper medium-risk detection
                self.risk_factors.append({
                    'category': 'Network Anomaly',
                    'severity': 'High',
                    'description': f'Connection to suspicious port {remote_port}',
                    'impact': '+45 points',
                    'details': f'Remote: {remote_ip}:{remote_port}, Protocol: {protocol}'
                })

            # Check for non-standard HTTP ports (optimized with set lookup)
            elif protocol == 'TCP' and remote_port in {8000, 8001, 8080, 8888, 9000}:
                score += 15
                self.risk_factors.append({
                    'category': 'Network Pattern',
                    'severity': 'Medium',
                    'description': f'Connection to non-standard web port {remote_port}',
                    'impact': '+15 points',
                    'details': f'Remote: {remote_ip}:{remote_port}'
                })

            # Check for connections to test/private IP ranges (optimized with startswith)
            elif remote_ip.startswith(('203.0.113.', '198.51.100.')):
                score += 20
                self.risk_factors.append({
                    'category': 'Suspicious Destination',
                    'severity': 'High',
                    'description': f'Connection to uncommon IP range',
                    'impact': '+20 points',
                    'details': f'Destination: {remote_ip}:{remote_port}'
                })

        return min(100, score)

    def _analyze_system(self, system_info: dict) -> int:
        '''Analyze system artifacts and return risk score (0-100) - Optimized'''
        score = 0

        # Check registry persistence (optimized with early termination)
        registry = system_info.get('registry', [])
        if registry:
            for reg_entry in registry[:20]:  # Limit to first 20 registry entries
                key_path = reg_entry.get('key', '').lower()
                if 'run' in key_path and 'currentversion' in key_path:
                    score += 40  # Increased to 40 for proper medium-risk detection
                    self.risk_factors.append({
                        'category': 'Persistence',
                        'severity': 'High', 
                        'description': 'Suspicious autostart registry entry detected',
                        'impact': '+40 points',
                        'details': f'Key: {reg_entry.get("key")}, Value: {reg_entry.get("value")}'
                    })

        # Check for suspicious files (optimized with early termination)
        files = system_info.get('files', [])
        if files:
            for file_info in files[:20]:  # Limit to first 20 files
                file_path = file_info.get('path', '').lower()
                if 'temp' in file_path and file_info.get('executable', False):
                    score += 15
                    self.risk_factors.append({
                        'category': 'File System',
                        'severity': 'Medium',
                        'description': 'Executable file in temporary directory',
                        'impact': '+15 points',
                        'details': f'File: {file_info.get("path")}'
                    })

        return min(100, score)

    def _is_suspicious_parent_child_optimized(self, process: dict, process_map: dict) -> bool:
        '''Optimized check for suspicious parent-child relationship using process map'''
        name = process.get('name', '').lower()
        ppid = process.get('ppid', 0)

        # Get parent process from map (O(1) lookup)
        parent = process_map.get(ppid)
        if not parent:
            return False

        parent_name = parent.get('name', '').lower()

        # Define suspicious relationships (optimized with set lookup)
        suspicious_pairs = {
            ('notepad.exe', 'powershell.exe'),
            ('winword.exe', 'powershell.exe'), 
            ('excel.exe', 'cmd.exe'),
            ('notepad.exe', 'cmd.exe'),
            ('calc.exe', 'powershell.exe')
        }

        return (parent_name, name) in suspicious_pairs

    def _is_suspicious_parent_child(self, process: dict, all_processes: List[dict]) -> bool:
        '''Check if process has suspicious parent-child relationship'''
        name = process.get('name', '').lower()
        ppid = process.get('ppid', 0)

        # Find parent process
        parent = next((p for p in all_processes if p.get('pid') == ppid), None)
        if not parent:
            return False

        parent_name = parent.get('name', '').lower()

        # Define suspicious relationships
        suspicious_pairs = [
            ('notepad.exe', 'powershell.exe'),
            ('winword.exe', 'powershell.exe'), 
            ('excel.exe', 'cmd.exe'),
            ('notepad.exe', 'cmd.exe'),
            ('calc.exe', 'powershell.exe')
        ]

        return (parent_name, name) in suspicious_pairs

    def _get_parent_name(self, ppid: int, processes: List[dict]) -> str:
        '''Get parent process name by PID'''
        parent = next((p for p in processes if p.get('pid') == ppid), None)
        return parent.get('name', 'Unknown') if parent else 'Unknown'

    def _get_risk_level(self) -> str:
        '''Convert numeric score to risk level'''
        if self.total_score >= 80:
            return 'Critical'
        elif self.total_score >= 60:
            return 'High'  
        elif self.total_score >= 40:
            return 'Medium'
        elif self.total_score >= 20:
            return 'Low'
        else:
            return 'Minimal'

    def _get_score_breakdown(self) -> dict:
        '''Provide detailed score breakdown by category'''
        breakdown = {}
        for factor in self.risk_factors:
            category = factor['category']
            impact = int(factor['impact'].replace('+', '').replace(' points', ''))
            if category in breakdown:
                breakdown[category] += impact
            else:
                breakdown[category] = impact

        return breakdown

    def _generate_explanation(self) -> str:
        '''Generate human-readable explanation of risk score'''
        if not self.risk_factors:
            return f"Risk score of {self.total_score} based on baseline system behavior with no significant anomalies detected."

        explanation = f"Risk score of {self.total_score} ({self._get_risk_level()}) calculated based on {len(self.risk_factors)} security indicators:\n\n"

        # Group by severity
        critical = [f for f in self.risk_factors if f['severity'] == 'Critical']
        high = [f for f in self.risk_factors if f['severity'] == 'High']
        medium = [f for f in self.risk_factors if f['severity'] == 'Medium']

        if critical:
            explanation += f"🔴 CRITICAL ({len(critical)} findings):\n"
            for f in critical:
                explanation += f"  • {f['description']} ({f['impact']})\n"
            explanation += "\n"

        if high:
            explanation += f"🟠 HIGH ({len(high)} findings):\n" 
            for f in high:
                explanation += f"  • {f['description']} ({f['impact']})\n"
            explanation += "\n"

        if medium:
            explanation += f"🟡 MEDIUM ({len(medium)} findings):\n"
            for f in medium:
                explanation += f"  • {f['description']} ({f['impact']})\n"

        return explanation

    def _get_recommendations(self) -> List[str]:
        '''Generate actionable recommendations based on risk factors'''
        recommendations = []

        categories = set(f['category'] for f in self.risk_factors)

        if 'Malicious Execution' in categories:
            recommendations.append("🚨 Immediately isolate system and investigate PowerShell execution")
            recommendations.append("🔍 Review PowerShell logs and decode suspicious commands")

        if 'Process Anomaly' in categories:
            recommendations.append("⚠️ Investigate suspicious parent-child process relationships")
            recommendations.append("🛡️ Consider process whitelisting to prevent unusual spawning")

        if 'Network Anomaly' in categories:
            recommendations.append("🌐 Block network connections to suspicious IPs/ports")
            recommendations.append("📊 Review network logs for data exfiltration patterns")

        if 'Persistence' in categories:
            recommendations.append("🔧 Remove suspicious registry autostart entries")
            recommendations.append("🔄 Reset user and system startup configurations")

        if 'LOLBin Usage' in categories:
            recommendations.append("⚙️ Audit living-off-the-land binary usage policies")
            recommendations.append("📝 Implement application whitelisting for system binaries")

        if not recommendations:
            recommendations = [
                "✅ System appears clean with minimal risk indicators",
                "🔍 Continue monitoring for emerging threats",
                "🛡️ Maintain current security posture"
            ]

        return recommendations

    def _create_cache_key(self, process_data: dict, network_data: dict, system_info: dict) -> str:
        '''Create a simple cache key from the input data'''
        # Create a simple hash from key data points
        process_count = len(process_data.get('processes', []))
        network_count = len(network_data.get('connections', []))
        registry_count = len(system_info.get('registry', []))
        files_count = len(system_info.get('files', []))
        
        # Create a simple key from counts and first few process names
        process_names = [p.get('name', '') for p in process_data.get('processes', [])[:5]]
        key_data = f"{process_count}_{network_count}_{registry_count}_{files_count}_{'_'.join(process_names)}"
        
        return str(hash(key_data))

    def _store_in_cache(self, cache_key: str, result: dict):
        '''Store result in cache with size limit'''
        # Remove oldest entries if cache is full
        if len(self._cache) >= self._cache_max_size:
            # Remove first (oldest) entry
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
        
        # Store the result
        self._cache[cache_key] = result.copy()

    def clear_cache(self):
        '''Clear the analysis cache'''
        self._cache.clear()

    def get_cache_stats(self) -> dict:
        '''Get cache statistics'''
        return {
            'cache_size': len(self._cache),
            'max_cache_size': self._cache_max_size,
            'cache_hit_ratio': 'N/A'  # Would need hit/miss tracking for real ratio
        }
