#!/usr/bin/env python3
"""
volLite Application Runner
Enhanced version with database initialization and health checks
"""

import os
import sys
from app import create_app
from utils.database import init_database, check_database_connection

def main():
    """Main application entry point"""
    print("volLite - AI-Based Memory Forensics Assistant")
    print("=" * 50)

    # Create app
    app = create_app()

    # Check database connection
    with app.app_context():
        print("Checking database connection...")
        db_status = check_database_connection()

        if db_status['status'] == 'connected':
            print("✓ Database connection successful")
        else:
            print(f"✗ Database connection failed: {db_status['error']}")
            print("Please check your database configuration in .env file")
            return 1

        # Initialize database
        print("Initializing database...")
        if init_database():
            print("✓ Database initialized successfully")
        else:
            print("✗ Database initialization failed")
            return 1

    # Create upload directory
    upload_dir = app.config['UPLOAD_FOLDER']
    os.makedirs(upload_dir, exist_ok=True)
    print(f"✓ Upload directory ready: {upload_dir}")

    # Check Volatility availability
    from services.volatility_service import VolatilityService
    vol_service = VolatilityService()
    vol_status = vol_service.check_volatility_available()

    if vol_status['available']:
        print(f"✓ Volatility available: {vol_status.get('version', 'unknown version')}")
    else:
        print(f"⚠ Volatility not available: {vol_status['error']}")
        print("  Some analysis features may not work properly")

    print("\nStarting volLite server...")
    print(f"Server will be available at: http://localhost:{os.environ.get('PORT', 5000)}")
    print("Press Ctrl+C to stop")
    print("=" * 50)

    # Run application
    try:
        app.run(
            debug=app.config.get('DEBUG', False),
            host='0.0.0.0',
            port=int(os.environ.get('PORT', 5000))
        )
    except KeyboardInterrupt:
        print("\n\nShutting down volLite server...")
        return 0
    except Exception as e:
        print(f"\nError starting server: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())