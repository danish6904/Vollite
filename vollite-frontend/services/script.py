# Continue creating Phase 1 files - Services and Utilities

phase1_services = {
    "services/__init__.py": """# Services package initialization""",
    
    "services/file_validator.py": """import os
import hashlib
import magic
from werkzeug.utils import secure_filename
from pathlib import Path

class FileValidator:
    def __init__(self, max_size=2*1024*1024*1024, allowed_extensions=None):  # 2GB default
        self.max_size = max_size
        self.allowed_extensions = allowed_extensions or {'dmp', 'mem', 'raw', 'vmem', 'bin'}
        self.allowed_mime_types = {
            'application/octet-stream',
            'application/x-dmp',
            'application/x-vmware-vmem',
            'application/x-raw',
            'binary/octet-stream'
        }
    
    def validate_file(self, file, file_path=None):
        \"\"\"Comprehensive file validation\"\"\"
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'file_info': {}
        }
        
        # Basic file checks
        if not file or not file.filename:
            validation_result['valid'] = False
            validation_result['errors'].append('No file provided')
            return validation_result
        
        # Secure filename
        original_filename = file.filename
        secure_name = secure_filename(original_filename)
        
        if not secure_name:
            validation_result['valid'] = False
            validation_result['errors'].append('Invalid filename')
            return validation_result
        
        validation_result['file_info']['original_filename'] = original_filename
        validation_result['file_info']['secure_filename'] = secure_name
        
        # Check file extension
        file_ext = Path(original_filename).suffix.lower().lstrip('.')
        if file_ext not in self.allowed_extensions:
            validation_result['warnings'].append(f'Unusual file extension: .{file_ext}')
        
        # If file is saved, perform additional checks
        if file_path and os.path.exists(file_path):
            # File size check
            file_size = os.path.getsize(file_path)
            validation_result['file_info']['file_size'] = file_size
            
            if file_size > self.max_size:
                validation_result['valid'] = False
                validation_result['errors'].append(f'File too large: {file_size} bytes (max: {self.max_size})')
            
            if file_size < 1024:  # Less than 1KB
                validation_result['warnings'].append('File suspiciously small for memory dump')
            
            # MIME type check
            try:
                mime_type = magic.from_file(file_path, mime=True)
                validation_result['file_info']['mime_type'] = mime_type
                
                if mime_type not in self.allowed_mime_types:
                    validation_result['warnings'].append(f'Unusual MIME type: {mime_type}')
            except Exception as e:
                validation_result['warnings'].append(f'Could not determine MIME type: {str(e)}')
            
            # Calculate file hash
            try:
                file_hash = self._calculate_sha256(file_path)
                validation_result['file_info']['sha256'] = file_hash
            except Exception as e:
                validation_result['errors'].append(f'Error calculating file hash: {str(e)}')
            
            # Basic memory dump validation
            dump_check = self._check_memory_dump_structure(file_path)
            validation_result['file_info']['dump_type'] = dump_check.get('type', 'unknown')
            
            if not dump_check.get('valid', False):
                validation_result['warnings'].append('File may not be a valid memory dump')
        
        return validation_result
    
    def _calculate_sha256(self, file_path):
        \"\"\"Calculate SHA256 hash of file\"\"\"
        hash_sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            # Read in chunks to handle large files
            for chunk in iter(lambda: f.read(8192), b''):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    def _check_memory_dump_structure(self, file_path):
        \"\"\"Basic validation of memory dump structure\"\"\"
        result = {'valid': False, 'type': 'unknown'}
        
        try:
            with open(file_path, 'rb') as f:
                header = f.read(2048)  # Read first 2KB
                
                # Check for common memory dump signatures
                if len(header) >= 6 and header[:6] == b'PAGEDU':
                    result = {'valid': True, 'type': 'windows_crash_dump'}
                elif len(header) >= 4 and header[:4] == b'HIBR':
                    result = {'valid': True, 'type': 'windows_hibernation'}
                elif len(header) >= 8 and header[:8] == b'KDMP' + b'\\x00' * 4:
                    result = {'valid': True, 'type': 'windows_kernel_dump'}
                elif header.startswith(b'\\x00' * 16):  # Might be raw memory
                    result = {'valid': True, 'type': 'raw_memory'}
                else:
                    # Check for VMware memory files
                    if b'.vmem' in str(file_path).lower().encode():
                        result = {'valid': True, 'type': 'vmware_memory'}
                    else:
                        result = {'valid': False, 'type': 'unknown_format'}
                        
        except Exception as e:
            result = {'valid': False, 'type': 'error', 'error': str(e)}
        
        return result

    @staticmethod
    def generate_secure_filename(original_filename, session_id=None):
        \"\"\"Generate a secure filename for storage\"\"\"
        import uuid
        from datetime import datetime
        
        # Get file extension
        file_ext = Path(original_filename).suffix.lower()
        
        # Generate unique filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_id = str(uuid.uuid4())[:8]
        
        if session_id:
            secure_name = f"session_{session_id}_{timestamp}_{unique_id}{file_ext}"
        else:
            secure_name = f"upload_{timestamp}_{unique_id}{file_ext}"
        
        return secure_name""",

    "services/volatility_service.py": """import subprocess
import json
import os
import tempfile
from pathlib import Path

class VolatilityService:
    def __init__(self, vol_path=None):
        self.vol_path = vol_path or self._find_volatility()
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
        \"\"\"Try to find Volatility installation\"\"\"
        possible_paths = [
            '/usr/local/bin/vol.py',
            '/usr/bin/vol.py',
            './volatility3/vol.py',
            'vol.py'
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        # Try to find in PATH
        try:
            result = subprocess.run(['which', 'vol.py'], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
        
        return None
    
    def check_volatility_available(self):
        \"\"\"Check if Volatility is available and working\"\"\"
        if not self.vol_path or not os.path.exists(self.vol_path):
            return {'available': False, 'error': 'Volatility not found'}
        
        try:
            # Test basic volatility command
            result = subprocess.run(
                ['python', self.vol_path, '--help'],
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
        \"\"\"Get Volatility version\"\"\"
        try:
            result = subprocess.run(
                ['python', self.vol_path, '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.stdout.strip() if result.returncode == 0 else 'unknown'
        except:
            return 'unknown'
    
    def detect_profile(self, dump_path):
        \"\"\"Attempt to detect the appropriate profile for the memory dump\"\"\"
        try:
            # Try imageinfo plugin (Volatility 2 style)
            result = subprocess.run([
                'python', self.vol_path,
                '-f', dump_path,
                'windows.info'
            ], capture_output=True, text=True, timeout=30)
            
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
            
        except Exception as e:
            print(f"Profile detection error: {e}")
        
        return 'Win10x64_19041'  # Default profile
    
    def basic_analysis(self, dump_path, profile=None):
        \"\"\"Perform basic memory dump analysis\"\"\"
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
            analysis_results['status'] = 'error'
            analysis_results['errors'].append(str(e))
        
        return analysis_results
    
    def _get_system_info(self, dump_path):
        \"\"\"Get basic system information\"\"\"
        try:
            result = subprocess.run([
                'python', self.vol_path,
                '-f', dump_path,
                'windows.info'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                return self._parse_system_info(result.stdout)
            else:
                return {'error': 'Could not retrieve system info', 'stderr': result.stderr}
                
        except subprocess.TimeoutExpired:
            return {'error': 'System info command timed out'}
        except Exception as e:
            return {'error': f'System info error: {str(e)}'}
    
    def _get_processes(self, dump_path):
        \"\"\"Get process list\"\"\"
        try:
            result = subprocess.run([
                'python', self.vol_path,
                '-f', dump_path,
                'windows.pslist'
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                return self._parse_processes(result.stdout)
            else:
                return [{'error': 'Could not retrieve process list', 'stderr': result.stderr}]
                
        except subprocess.TimeoutExpired:
            return [{'error': 'Process list command timed out'}]
        except Exception as e:
            return [{'error': f'Process list error: {str(e)}'}]
    
    def _get_network_connections(self, dump_path):
        \"\"\"Get network connections\"\"\"
        try:
            result = subprocess.run([
                'python', self.vol_path,
                '-f', dump_path,
                'windows.netstat'
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                return self._parse_network_connections(result.stdout)
            else:
                return [{'error': 'Could not retrieve network connections', 'stderr': result.stderr}]
                
        except subprocess.TimeoutExpired:
            return [{'error': 'Network connections command timed out'}]
        except Exception as e:
            return [{'error': f'Network connections error: {str(e)}'}]
    
    def _parse_system_info(self, output):
        \"\"\"Parse system info output\"\"\"
        info = {}
        lines = output.split('\\n')
        
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                info[key.strip().lower().replace(' ', '_')] = value.strip()
        
        return info
    
    def _parse_processes(self, output):
        \"\"\"Parse process list output\"\"\"
        processes = []
        lines = output.split('\\n')
        
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
                    except (ValueError, IndexError):
                        continue
        
        return processes
    
    def _parse_network_connections(self, output):
        \"\"\"Parse network connections output\"\"\"
        connections = []
        lines = output.split('\\n')
        
        for line in lines:
            if line.strip() and 'TCP' in line or 'UDP' in line:
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
                    except (ValueError, IndexError):
                        continue
        
        return connections""",

    "utils/__init__.py": """# Utilities package initialization""",
    
    "utils/security.py": """import os
import secrets
from functools import wraps
from flask import request, jsonify, current_app
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from models.user import User

def generate_secure_filename(original_filename, prefix='upload'):
    \"\"\"Generate a secure filename\"\"\"
    import uuid
    from datetime import datetime
    from pathlib import Path
    
    # Get file extension
    file_ext = Path(original_filename).suffix.lower()
    
    # Generate secure filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    unique_id = str(uuid.uuid4())[:8]
    
    return f"{prefix}_{timestamp}_{unique_id}{file_ext}"

def sanitize_filename(filename):
    \"\"\"Sanitize filename for safe storage\"\"\"
    import re
    
    # Remove directory path
    filename = os.path.basename(filename)
    
    # Replace dangerous characters
    filename = re.sub(r'[^\\w\\-_\\.]', '_', filename)
    
    # Limit length
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:250] + ext
    
    return filename

def validate_file_size(file_size, max_size=None):
    \"\"\"Validate file size\"\"\"
    if max_size is None:
        max_size = current_app.config.get('MAX_CONTENT_LENGTH', 2*1024*1024*1024)
    
    return file_size <= max_size

def secure_delete_file(file_path):
    \"\"\"Securely delete a file\"\"\"
    try:
        if os.path.exists(file_path):
            # Overwrite with random data (simple version)
            file_size = os.path.getsize(file_path)
            
            with open(file_path, 'r+b') as f:
                f.write(secrets.token_bytes(file_size))
                f.flush()
                os.fsync(f.fileno())
            
            # Remove the file
            os.remove(file_path)
            return True
    except Exception as e:
        print(f"Error securely deleting file {file_path}: {e}")
        return False
    
    return False

def require_auth(f):
    \"\"\"Decorator to require authentication\"\"\"
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            verify_jwt_in_request()
            user_id = get_jwt_identity()
            
            # Verify user exists and is active
            user = User.query.filter_by(id=user_id, is_active=True).first()
            if not user:
                return jsonify({'error': 'Invalid or inactive user'}), 401
            
            return f(*args, **kwargs)
        except Exception as e:
            return jsonify({'error': 'Authentication required'}), 401
    
    return decorated_function

def validate_json_request(required_fields=None):
    \"\"\"Decorator to validate JSON request data\"\"\"
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_json:
                return jsonify({'error': 'Content-Type must be application/json'}), 400
            
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No JSON data provided'}), 400
            
            if required_fields:
                missing_fields = [field for field in required_fields if field not in data]
                if missing_fields:
                    return jsonify({
                        'error': 'Missing required fields',
                        'missing_fields': missing_fields
                    }), 400
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

class SecurityHeaders:
    \"\"\"Security headers middleware\"\"\"
    
    @staticmethod
    def add_security_headers(response):
        \"\"\"Add security headers to response\"\"\"
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        return response""",

    "utils/database.py": """from models import db
from flask import current_app
import os

def init_database():
    \"\"\"Initialize database tables\"\"\"
    try:
        # Create tables if they don't exist
        db.create_all()
        print("Database tables created successfully")
        return True
    except Exception as e:
        print(f"Error creating database tables: {e}")
        return False

def reset_database():
    \"\"\"Reset database (drop and recreate all tables)\"\"\"
    try:
        # Drop all tables
        db.drop_all()
        # Create all tables
        db.create_all()
        print("Database reset successfully")
        return True
    except Exception as e:
        print(f"Error resetting database: {e}")
        return False

def check_database_connection():
    \"\"\"Check if database connection is working\"\"\"
    try:
        # Try a simple query
        db.engine.execute('SELECT 1')
        return {'status': 'connected', 'error': None}
    except Exception as e:
        return {'status': 'error', 'error': str(e)}

def backup_database(backup_path=None):
    \"\"\"Create database backup (SQLite only)\"\"\"
    try:
        if 'sqlite' not in current_app.config['SQLALCHEMY_DATABASE_URI']:
            return {'status': 'error', 'error': 'Backup only supported for SQLite'}
        
        if not backup_path:
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = f'backup_vollite_{timestamp}.db'
        
        # Get source database path
        db_uri = current_app.config['SQLALCHEMY_DATABASE_URI']
        source_path = db_uri.replace('sqlite:///', '')
        
        # Copy database file
        import shutil
        shutil.copy2(source_path, backup_path)
        
        return {'status': 'success', 'backup_path': backup_path}
    except Exception as e:
        return {'status': 'error', 'error': str(e)}""",
}

for filename, content in phase1_services.items():
    # Create directory if needed
    if '/' in filename:
        directory = filename.split('/')[0]
        os.makedirs(directory, exist_ok=True)
    
    with open(filename, 'w') as f:
        f.write(content)
    print(f"✓ Created {filename}")

print(f"\nCreated {len(phase1_services)} service and utility files")