from datetime import datetime
from . import db

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
        """Update analysis status"""
        self.analysis_status = status
        if error_message:
            self.error_message = error_message
        db.session.commit()

    def to_dict(self):
        """Convert session to dictionary"""
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
    risk_score = db.Column(db.Integer, default=0)
    key_findings = db.Column(db.JSON)
    process_data = db.Column(db.JSON)
    network_data = db.Column(db.JSON)
    system_info = db.Column(db.JSON)
    ai_insights = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __init__(self, session_id, summary=None, risk_score=0):
        self.session_id = session_id
        self.summary = summary
        self.risk_score = risk_score
        self.key_findings = []
        self.process_data = {}
        self.network_data = {}
        self.system_info = {}
        self.ai_insights = {}

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
            'ai_insights': self.ai_insights,
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
        }
