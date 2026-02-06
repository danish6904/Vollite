import subprocess
import json
import os
import tempfile
import logging
from pathlib import Path

class VolatilityService:
    def __init__(self, vol_path=None):
        # Prefer module invocation on Windows: `python -m volatility3`
        self.vol_path = vol_path or self._find_volatility()
        self.logger = logging.getLogger(__name__)
        self.supported_profiles = [
            'Win10x64_19041',
            'Win10x64_18362',
            'Win10x64_17763',
            'Win10x64_16299',
            'Win10x64_15063',
            'Win7SP1x64',
            'Win7SP0x64',
            'Win8SP0x64',
            'WinXPSP2x86',
            'WinXPSP3x86'
        ]

    def _find_volatility(self):
        """Try to find Volatility installation or module.

        Returns one of:
        - 'module' if `python -m volatility3` is invokable
        - path to vol(.exe/.cmd) or vol.py if found on disk or PATH
        - None if not found
        """
        # First, try module invocation
        try:
            # Prefer module CLI entrypoint
            result = subprocess.run(
                ['python', '-m', 'volatility3.cli', '--help'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                return 'module'
        except Exception:
            pass

        # Try Windows console scripts in common venv locations
        windows_candidates = [
            os.path.join('.venv', 'Scripts', 'vol.exe'),
            os.path.join('.venv', 'Scripts', 'vol.cmd'),
            os.path.join('env', 'Scripts', 'vol.exe'),
            os.path.join('env', 'Scripts', 'vol.cmd'),
            'vol.exe',
            'vol.cmd',
            'vol'
        ]

        for path in windows_candidates:
            if os.path.exists(path):
                return path

        # Try PATH for 'vol'
        try:
            from shutil import which
            vol_path = which('vol')
            if vol_path:
                return vol_path
        except Exception:
            pass

        # Then, try known script paths
        possible_paths = [
            '/usr/local/bin/vol.py',
            '/usr/bin/vol.py',
            './volatility3/vol.py',
            'vol.py'
        ]

        for path in possible_paths:
            if os.path.exists(path):
                return path

        # Try to find in PATH (Unix)
        try:
            result = subprocess.run(['which', 'vol.py'], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass

        return None

    def _build_cmd(self, *plugin_args):
        """Build the volatility command depending on availability."""
        if self.vol_path == 'module' or self.vol_path is None:
            # Default to module; availability check will catch errors
            return ['python', '-m', 'volatility3.cli', *plugin_args]
        # If using Windows console script or generic 'vol', call directly
        lower = self.vol_path.lower()
        if lower.endswith('.exe') or lower.endswith('.cmd') or os.path.basename(lower) == 'vol':
            return [self.vol_path, *plugin_args]
        # Otherwise assume a python script path
        return ['python', self.vol_path, *plugin_args]

    def check_volatility_available(self):
        """Check if Volatility is available and working"""
        # For module mode, skip path existence check
        if self.vol_path != 'module' and (not self.vol_path or not os.path.exists(self.vol_path)):
            return {'available': False, 'error': 'Volatility not found'}

        try:
            # Test basic volatility command
            result = subprocess.run(
                self._build_cmd('--help'),
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                return {'available': True, 'version': self._get_volatility_version()}
            else:
                return {'available': False, 'error': 'Volatility command failed'}

        except subprocess.TimeoutExpired:
            return {'available': False, 'error': 'Volatility command timed out'}
        except Exception as e:
            return {'available': False, 'error': f'Error running Volatility: {str(e)}'}

    def _get_volatility_version(self):
        """Get Volatility version"""
        try:
            result = subprocess.run(
                self._build_cmd('--version'),
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.stdout.strip() if result.returncode == 0 else 'unknown'
        except:
            return 'unknown'

    def detect_profile(self, dump_path):
        """Attempt to detect the appropriate profile for the memory dump"""
        if not os.path.isfile(dump_path):
            self.logger.error(f"Dump file does not exist: {dump_path}")
            return 'Win10x64_19041'  # Default profile

        try:
            # Try imageinfo plugin (Volatility 2 style)
            result = subprocess.run(
                self._build_cmd('-f', dump_path, 'windows.info'),
                capture_output=True, text=True, timeout=30
            )

            if result.returncode == 0:
                # Parse output to determine OS version
                output = result.stdout.lower()

                # Simple profile detection logic
                if 'windows 10' in output:
                    return 'Win10x64_19041'
                elif 'windows 7' in output:
                    return 'Win7SP1x64'
                elif 'windows 8' in output:
                    return 'Win8SP0x64'
                elif 'windows xp' in output:
                    return 'WinXPSP3x86'
                else:
                    return 'Win10x64_19041'  # Default fallback

            else:
                self.logger.error(f"Profile detection failed with return code {result.returncode}: {result.stderr}")

        except subprocess.TimeoutExpired:
            self.logger.error("Profile detection command timed out")
        except Exception as e:
            self.logger.error(f"Profile detection error: {e}")

        return 'Win10x64_19041'  # Default profile

    def basic_analysis(self, dump_path, profile=None):
        """Perform basic memory dump analysis"""
        if not os.path.isfile(dump_path):
            self.logger.error(f"Dump file does not exist: {dump_path}")
            return {
                'profile': 'unknown',
                'system_info': {},
                'processes': [],
                'network': [],
                'status': 'error',
                'errors': [f"Dump file does not exist: {dump_path}"]
            }

        if not profile:
            profile = self.detect_profile(dump_path)

        analysis_results = {
            'profile': profile,
            'system_info': {},
            'processes': [],
            'network': [],
            'status': 'success',
            'errors': []
        }

        try:
            # Get system information
            system_info = self._get_system_info(dump_path)
            analysis_results['system_info'] = system_info

            # Get process list
            processes = self._get_processes(dump_path)
            analysis_results['processes'] = processes

            # Get network connections
            network = self._get_network_connections(dump_path)
            analysis_results['network'] = network

        except Exception as e:
            self.logger.error(f"Basic analysis error: {e}")
            analysis_results['status'] = 'error'
            analysis_results['errors'].append(str(e))

        return analysis_results

    def run_plugins(self, dump_path: str, plugins: list[str], extra_args: list[str] | None = None):
        """Run specified volatility plugins and return raw outputs.

        Returns dict: { plugin_name: { 'returncode': int, 'stdout': str, 'stderr': str } }
        """
        results: dict[str, dict] = {}
        if extra_args is None:
            extra_args = []

        if not os.path.isfile(dump_path):
            return { 'error': f'Dump file does not exist: {dump_path}' }

        for plugin in plugins:
            try:
                cmd = self._build_cmd('-f', dump_path, plugin, *extra_args)
                proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                results[plugin] = {
                    'returncode': proc.returncode,
                    'stdout': proc.stdout,
                    'stderr': proc.stderr
                }
            except subprocess.TimeoutExpired:
                results[plugin] = {
                    'returncode': -1,
                    'stdout': '',
                    'stderr': 'Plugin execution timed out'
                }
            except Exception as e:
                results[plugin] = {
                    'returncode': -1,
                    'stdout': '',
                    'stderr': f'Error running plugin: {e}'
                }

        return results

    def _get_system_info(self, dump_path):
        """Get basic system information"""
        try:
            result = subprocess.run(
                self._build_cmd('-f', dump_path, 'windows.info'),
                capture_output=True, text=True, timeout=30
            )

            if result.returncode == 0:
                return self._parse_system_info(result.stdout)
            else:
                self.logger.error(f"System info retrieval failed: {result.stderr}")
                return {'error': 'Could not retrieve system info', 'stderr': result.stderr}

        except subprocess.TimeoutExpired:
            self.logger.error("System info command timed out")
            return {'error': 'System info command timed out'}
        except Exception as e:
            self.logger.error(f"System info error: {e}")
            return {'error': f'System info error: {str(e)}'}

    def _get_processes(self, dump_path):
        """Get process list"""
        try:
            result = subprocess.run(
                self._build_cmd('-f', dump_path, 'windows.pslist'),
                capture_output=True, text=True, timeout=60
            )

            if result.returncode == 0:
                return self._parse_processes(result.stdout)
            else:
                self.logger.error(f"Process list retrieval failed: {result.stderr}")
                return [{'error': 'Could not retrieve process list', 'stderr': result.stderr}]

        except subprocess.TimeoutExpired:
            self.logger.error("Process list command timed out")
            return [{'error': 'Process list command timed out'}]
        except Exception as e:
            self.logger.error(f"Process list error: {e}")
            return [{'error': f'Process list error: {str(e)}'}]

    def _get_network_connections(self, dump_path):
        """Get network connections"""
        try:
            result = subprocess.run(
                self._build_cmd('-f', dump_path, 'windows.netstat'),
                capture_output=True, text=True, timeout=60
            )

            if result.returncode == 0:
                return self._parse_network_connections(result.stdout)
            else:
                self.logger.error(f"Network connections retrieval failed: {result.stderr}")
                return [{'error': 'Could not retrieve network connections', 'stderr': result.stderr}]

        except subprocess.TimeoutExpired:
            self.logger.error("Network connections command timed out")
            return [{'error': 'Network connections command timed out'}]
        except Exception as e:
            self.logger.error(f"Network connections error: {e}")
            return [{'error': f'Network connections error: {str(e)}'}]

    def _parse_system_info(self, output):
        """Parse system info output"""
        info = {}
        lines = output.split('\n')

        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                info[key.strip().lower().replace(' ', '_')] = value.strip()

        return info

    def _parse_processes(self, output):
        """Parse process list output"""
        processes = []
        lines = output.split('\n')

        # Skip header lines and parse process data
        header_found = False
        for line in lines:
            if 'PID' in line and 'PPID' in line:
                header_found = True
                continue

            if header_found and line.strip():
                parts = line.split()
                if len(parts) >= 4:
                    try:
                        process = {
                            'pid': int(parts[0]),
                            'ppid': int(parts[1]),
                            'name': parts[2],
                            'start_time': ' '.join(parts[3:5]) if len(parts) >= 5 else 'N/A'
                        }
                        processes.append(process)
                    except (ValueError, IndexError) as e:
                        self.logger.warning(f"Failed to parse process line: {line.strip()} - {e}")
                        continue

        return processes

    def _parse_network_connections(self, output):
        """Parse network connections output"""
        connections = []
        lines = output.split('\n')

        for line in lines:
            if line.strip() and ('TCP' in line or 'UDP' in line):
                parts = line.split()
                if len(parts) >= 5:
                    try:
                        connection = {
                            'protocol': parts[0],
                            'local_addr': parts[1],
                            'foreign_addr': parts[2],
                            'state': parts[3] if len(parts) > 3 else 'N/A',
                            'pid': int(parts[4]) if len(parts) > 4 and parts[4].isdigit() else 0
                        }
                        connections.append(connection)
                    except (ValueError, IndexError) as e:
                        self.logger.warning(f"Failed to parse network line: {line.strip()} - {e}")
                        continue

        return connections
