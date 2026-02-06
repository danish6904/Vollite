# API package initialization
from flask import Blueprint

def register_blueprints(app):
    """Register all API blueprints"""
    from .auth import auth_bp
    from .analysis import analysis_bp
    from .enhanced_analysis_endpoints import enhanced_analysis_bp
    from .rag import rag_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(analysis_bp, url_prefix='/api/analysis')
    app.register_blueprint(enhanced_analysis_bp, url_prefix='/api/analysis')
    app.register_blueprint(rag_bp)
