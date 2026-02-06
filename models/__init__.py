from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager

# Initialize extensions
db = SQLAlchemy()
bcrypt = Bcrypt()
jwt = JWTManager()

def init_db(app):
    """Initialize database with Flask app"""
    db.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)
    
# Import models after db is defined to avoid circular imports
from .user import User
from .analysis import AnalysisSession, AnalysisResult, Alert
