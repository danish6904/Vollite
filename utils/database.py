from models import db
from flask import current_app
import os
import logging

logger = logging.getLogger(__name__)

def init_database():
    """Initialize database tables"""
    try:
        # Create tables if they don't exist
        db.create_all()
        logger.info("Database tables created successfully")
        return True
    except Exception as e:
        logger.exception("Error creating database tables")
        return False

def reset_database():
    """Reset database (drop and recreate all tables)"""
    try:
        # Drop all tables
        db.drop_all()
        # Create all tables
        db.create_all()
        logger.info("Database reset successfully")
        return True
    except Exception as e:
        logger.exception("Error resetting database")
        return False

def check_database_connection():
    """Check if database connection is working"""
    try:
        # SQLAlchemy 2.x style connection and execution
        with db.engine.connect() as connection:
            result = connection.exec_driver_sql('SELECT 1')
            _ = result.scalar()
        return {'status': 'connected', 'error': None}
    except Exception as e:
        return {'status': 'error', 'error': str(e)}

def backup_database(backup_path=None):
    """Create database backup (SQLite only)"""
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
        return {'status': 'error', 'error': str(e)}