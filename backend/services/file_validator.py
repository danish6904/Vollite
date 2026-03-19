import os
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
        """Comprehensive file validation"""
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
        """Calculate SHA256 hash of file"""
        hash_sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            # Read in chunks to handle large files
            for chunk in iter(lambda: f.read(8192), b''):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()

    def _check_memory_dump_structure(self, file_path):
        """Basic validation of memory dump structure"""
        result = {'valid': False, 'type': 'unknown'}

        try:
            with open(file_path, 'rb') as f:
                header = f.read(2048)  # Read first 2KB

                # Check for common memory dump signatures
                if len(header) >= 6 and header[:6] == b'PAGEDU':
                    result = {'valid': True, 'type': 'windows_crash_dump'}
                elif len(header) >= 4 and header[:4] == b'HIBR':
                    result = {'valid': True, 'type': 'windows_hibernation'}
                elif len(header) >= 8 and header[:8] == b'KDMP' + b'\x00' * 4:
                    result = {'valid': True, 'type': 'windows_kernel_dump'}
                elif header.startswith(b'\x00' * 16):  # Might be raw memory
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
        """Generate a secure filename for storage"""
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

        return secure_name