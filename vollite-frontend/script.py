# Let me create the complete Phase 1 implementation with all necessary code files

print("Creating Phase 1 Implementation Files for volLite")
print("=" * 60)

# Let's create a comprehensive file structure for Phase 1
phase1_files = {
    "requirements.txt": """# Phase 1 Requirements for volLite
Flask==3.0.0
Flask-SQLAlchemy==3.1.1
Flask-JWT-Extended==4.6.0
Flask-Bcrypt==1.0.1
Flask-CORS==4.0.0
Flask-Migrate==4.0.5
psycopg2-binary==2.9.9
python-dotenv==1.0.0
python-magic==0.4.27
Werkzeug==3.0.1
volatility3==2.5.0
""",
    
    "config.py": """import os
from datetime import timedelta

class Config:
    # Basic Flask configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database configuration
    DATABASE_URL = os.environ.get('DATABASE_URL') or 'sqlite:///vollite.db'
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT configuration
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or SECRET_KEY
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
    # File upload configuration
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024 * 1024  # 2GB max file size
    ALLOWED_EXTENSIONS = {'dmp', 'mem', 'raw', 'vmem'}
    
    # Security configuration
    BCRYPT_LOG_ROUNDS = 12
    
    # Volatility configuration
    VOLATILITY_PATH = os.environ.get('VOLATILITY_PATH') or '/usr/local/bin/vol.py'
    
    # CORS configuration
    CORS_ORIGINS = ['http://localhost:3000', 'http://127.0.0.1:3000']

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///vollite_dev.db'

class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}""",

    ".env": """# Environment variables for volLite
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here
DATABASE_URL=postgresql://username:password@localhost/vollite
VOLATILITY_PATH=/path/to/volatility3/vol.py
""",

    "models/__init__.py": """from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager

db = SQLAlchemy()
bcrypt = Bcrypt()
jwt = JWTManager()

def init_db(app):
    \"\"\"Initialize database with Flask app\"\"\"
    db.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)
""",

    "models/user.py": """from datetime import datetime
from models import db, bcrypt
from flask_jwt_extended import create_access_token, create_refresh_token

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    
    # Relationships
    analysis_sessions = db.relationship('AnalysisSession', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.set_password(password)
    
    def set_password(self, password):
        \"\"\"Hash and set password\"\"\"
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    
    def check_password(self, password):
        \"\"\"Check password against hash\"\"\"
        return bcrypt.check_password_hash(self.password_hash, password)
    
    def generate_tokens(self):
        \"\"\"Generate access and refresh tokens\"\"\"
        access_token = create_access_token(identity=self.id)
        refresh_token = create_refresh_token(identity=self.id)
        return {
            'access_token': access_token,
            'refresh_token': refresh_token
        }
    
    def to_dict(self):
        \"\"\"Convert user to dictionary\"\"\"
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat(),
            'is_active': self.is_active
        }
    
    def __repr__(self):
        return f'<User {self.username}>'""",

    "models/analysis.py": """from datetime import datetime
from models import db

class AnalysisSession(db.Model):
    __tablename__ = 'analysis_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_hash = db.Column(db.String(64), nullable=False, index=True)
    file_size = db.Column(db.BigInteger, nullable=False)
    mime_type = db.Column(db.String(100))
    upload_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    analysis_status = db.Column(db.String(20), nullable=False, default='uploaded')
    volatility_profile = db.Column(db.String(50))
    analysis_duration = db.Column(db.Integer)  # in seconds
    error_message = db.Column(db.Text)
    
    # Relationships
    results = db.relationship('AnalysisResult', backref='session', lazy=True, cascade='all, delete-orphan')
    alerts = db.relationship('Alert', backref='session', lazy=True, cascade='all, delete-orphan')
    
    def __init__(self, user_id, filename, original_filename, file_hash, file_size, mime_type=None):
        self.user_id = user_id
        self.filename = filename
        self.original_filename = original_filename
        self.file_hash = file_hash
        self.file_size = file_size
        self.mime_type = mime_type
    
    def update_status(self, status, error_message=None):
        \"\"\"Update analysis status\"\"\"
        self.analysis_status = status
        if error_message:
            self.error_message = error_message
        db.session.commit()
    
    def to_dict(self):
        \"\"\"Convert session to dictionary\"\"\"
        return {
            'id': self.id,
            'user_id': self.user_id,
            'filename': self.original_filename,
            'file_hash': self.file_hash,
            'file_size': self.file_size,
            'mime_type': self.mime_type,
            'upload_time': self.upload_time.isoformat(),
            'analysis_status': self.analysis_status,
            'volatility_profile': self.volatility_profile,
            'analysis_duration': self.analysis_duration,
            'error_message': self.error_message
        }
    
    def __repr__(self):
        return f'<AnalysisSession {self.id}: {self.original_filename}>'

class AnalysisResult(db.Model):
    __tablename__ = 'analysis_results'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('analysis_sessions.id'), nullable=False)
    summary = db.Column(db.Text)
    risk_score = db.Column(db.Integer)
    key_findings = db.Column(db.JSON)
    process_data = db.Column(db.JSON)
    network_data = db.Column(db.JSON)
    system_info = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    def __init__(self, session_id, summary=None, risk_score=0):
        self.session_id = session_id
        self.summary = summary
        self.risk_score = risk_score
    
    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'summary': self.summary,
            'risk_score': self.risk_score,
            'key_findings': self.key_findings,
            'process_data': self.process_data,
            'network_data': self.network_data,
            'system_info': self.system_info,
            'created_at': self.created_at.isoformat()
        }

class Alert(db.Model):
    __tablename__ = 'alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('analysis_sessions.id'), nullable=False)
    alert_type = db.Column(db.String(50), nullable=False)
    severity = db.Column(db.String(10), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    threat_indicators = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    def __init__(self, session_id, alert_type, severity, title, description, threat_indicators=None):
        self.session_id = session_id
        self.alert_type = alert_type
        self.severity = severity
        self.title = title
        self.description = description
        self.threat_indicators = threat_indicators or {}
    
    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'alert_type': self.alert_type,
            'severity': self.severity,
            'title': self.title,
            'description': self.description,
            'threat_indicators': self.threat_indicators,
            'created_at': self.created_at.isoformat()
        }""",
}

for filename, content in phase1_files.items():
    # Create directory if needed
    if '/' in filename:
        directory = filename.split('/')[0]
        os.makedirs(directory, exist_ok=True)
    
    with open(filename, 'w') as f:
        f.write(content)
    print(f"✓ Created {filename}")

print(f"\nCreated {len(phase1_files)} configuration and model files")