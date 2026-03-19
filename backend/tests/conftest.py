"""
Shared test fixtures for volLite test suite.
Provides a configured Flask test app, DB session, test client, and auth helpers.
"""

import os
import pytest
import tempfile

# Force test config before any app imports
os.environ['SECRET_KEY'] = 'test-secret-key'
os.environ['JWT_SECRET_KEY'] = 'test-jwt-secret-key'

from app import create_app
from models import db as _db
from models.user import User
from flask_jwt_extended import create_access_token

_UPLOAD_DIR = tempfile.mkdtemp()


@pytest.fixture(scope='session')
def app():
    """Create a Flask app once for the whole test session."""
    app = create_app('development')
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'  # in-memory
    app.config['JWT_SECRET_KEY'] = 'test-jwt-secret-key'
    app.config['SECRET_KEY'] = 'test-secret-key'
    app.config['UPLOAD_FOLDER'] = _UPLOAD_DIR
    app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024

    with app.app_context():
        _db.create_all()

    yield app


@pytest.fixture(autouse=True)
def _clean_tables(app):
    """Delete all rows from every table before each test."""
    with app.app_context():
        for table in reversed(_db.metadata.sorted_tables):
            _db.session.execute(table.delete())
        _db.session.commit()
    yield
    with app.app_context():
        _db.session.remove()


@pytest.fixture
def client(app):
    """Flask test client."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Flask CLI test runner."""
    return app.test_cli_runner()


# ── Auth Helpers ──────────────────────────────────────────────────────────

TEST_USER = {
    'username': 'testuser',
    'email': 'test@example.com',
    'password': 'TestPass123'
}


@pytest.fixture
def registered_user(client):
    """Register a test user via the API and return the response JSON."""
    resp = client.post('/api/auth/register', json=TEST_USER)
    return resp.get_json()


@pytest.fixture
def auth_header(app, client):
    """Create a test user directly in the DB and return a valid auth header."""
    with app.app_context():
        user = User(
            username='testuser',
            email='test@example.com',
            password='TestPass123'
        )
        _db.session.add(user)
        _db.session.commit()
        token = create_access_token(identity=str(user.id))
        return {'Authorization': f'Bearer {token}'}
