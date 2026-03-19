"""
Unit tests for services/file_validator.py

Tests file validation logic: extension checks, size checks, hash computation,
and memory dump structure detection.
"""

import os
import tempfile
import hashlib
import pytest

from services.file_validator import FileValidator


@pytest.fixture
def validator():
    return FileValidator()


class TestExtensionValidation:

    def test_allowed_extensions(self, validator):
        assert 'dmp' in validator.allowed_extensions
        assert 'mem' in validator.allowed_extensions
        assert 'raw' in validator.allowed_extensions
        assert 'vmem' in validator.allowed_extensions

    def test_unusual_extension_warns(self, validator):
        """A .zip file should still pass (not rejected) but emit a warning."""
        tmp = tempfile.NamedTemporaryFile(suffix='.zip', delete=False)
        tmp.write(b'\x00' * 2048)
        tmp.close()

        class FakeFile:
            filename = 'test.zip'

        result = validator.validate_file(FakeFile(), tmp.name)
        os.unlink(tmp.name)

        assert result['valid']  # not blocked, only warned
        assert any('Unusual file extension' in w for w in result['warnings'])


class TestSizeValidation:

    def test_small_file_warns(self, validator):
        """Files < 1KB should trigger a warning."""
        tmp = tempfile.NamedTemporaryFile(suffix='.dmp', delete=False)
        tmp.write(b'\x00' * 100)  # 100 bytes
        tmp.close()

        class FakeFile:
            filename = 'tiny.dmp'

        result = validator.validate_file(FakeFile(), tmp.name)
        os.unlink(tmp.name)

        assert any('small' in w.lower() for w in result['warnings'])

    def test_file_size_recorded(self, validator):
        tmp = tempfile.NamedTemporaryFile(suffix='.dmp', delete=False)
        tmp.write(b'\x00' * 4096)
        tmp.close()

        class FakeFile:
            filename = 'dump.dmp'

        result = validator.validate_file(FakeFile(), tmp.name)
        os.unlink(tmp.name)

        assert result['file_info']['file_size'] == 4096


class TestHashCalculation:

    def test_sha256_correct(self, validator):
        content = b'volatility test data'
        expected = hashlib.sha256(content).hexdigest()

        tmp = tempfile.NamedTemporaryFile(suffix='.dmp', delete=False)
        tmp.write(content)
        tmp.close()

        class FakeFile:
            filename = 'hash_test.dmp'

        result = validator.validate_file(FakeFile(), tmp.name)
        os.unlink(tmp.name)

        assert result['file_info']['sha256'] == expected


class TestNoFile:

    def test_no_filename(self, validator):
        class FakeFile:
            filename = ''

        result = validator.validate_file(FakeFile())
        assert not result['valid']

    def test_none_file(self, validator):
        result = validator.validate_file(None)
        assert not result['valid']


class TestDumpStructureDetection:

    def _write_and_check(self, validator, header_bytes, suffix='.dmp'):
        """Helper: write header bytes to a temp file and check structure."""
        tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
        # Pad to at least 2048 bytes so the header read succeeds
        tmp.write(header_bytes + b'\x00' * (2048 - len(header_bytes)))
        tmp.close()

        result = validator._check_memory_dump_structure(tmp.name)
        os.unlink(tmp.name)
        return result

    def test_windows_crash_dump(self, validator):
        result = self._write_and_check(validator, b'PAGEDU')
        assert result['valid']
        assert result['type'] == 'windows_crash_dump'

    def test_hibernation_file(self, validator):
        result = self._write_and_check(validator, b'HIBR')
        assert result['valid']
        assert result['type'] == 'windows_hibernation'

    def test_raw_memory(self, validator):
        result = self._write_and_check(validator, b'\x00' * 16)
        assert result['valid']
        assert result['type'] == 'raw_memory'

    def test_unknown_format(self, validator):
        result = self._write_and_check(validator, b'NOTADUMP')
        assert not result['valid']
        assert result['type'] == 'unknown_format'
