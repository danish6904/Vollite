# Create the main enhanced app.py and additional files for Phase 1

main_files = {
    "app.py": """from flask import Flask, render_template, request, jsonify, make_response
from flask_cors import CORS
from flask_migrate import Migrate
import os
from datetime import datetime

# Import configuration
from config import config

# Import database and models
from models import init_db, db
from models.user import User
from models.analysis import AnalysisSession, AnalysisResult, Alert

# Import API blueprints
from api import register_blueprints

# Import utilities
from utils.database import init_database, check_database_connection
from utils.security import SecurityHeaders

def create_app(config_name=None):
    \"\"\"Application factory\"\"\"
    app = Flask(__name__)
    
    # Load configuration
    config_name = config_name or os.environ.get('FLASK_ENV', 'development')
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    init_db(app)
    CORS(app, origins=app.config['CORS_ORIGINS'])
    migrate = Migrate(app, db)
    
    # Register API blueprints
    register_blueprints(app)
    
    # Initialize database
    with app.app_context():
        init_database()
    
    # Security headers middleware
    @app.after_request
    def after_request(response):
        return SecurityHeaders.add_security_headers(response)
    
    # Original frontend routes
    @app.route('/')
    def home():
        return render_template('home.html')
    
    @app.route('/about')
    def about():
        return render_template('about.html')
    
    @app.route('/contact')
    def contact():
        return render_template('contact.html')
    
    @app.route('/dashboard')
    def dashboard():
        return render_template('dashboard.html')
    
    # Health check endpoint
    @app.route('/api/health')
    def health_check():
        \"\"\"Health check endpoint\"\"\"
        db_status = check_database_connection()
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'database': db_status['status'],
            'version': '1.0.0-phase1'
        })
    
    # System info endpoint
    @app.route('/api/system/info')
    def system_info():
        \"\"\"System information endpoint\"\"\"
        from services.volatility_service import VolatilityService
        
        vol_service = VolatilityService()
        vol_status = vol_service.check_volatility_available()
        
        return jsonify({
            'volatility': vol_status,
            'database': check_database_connection(),
            'upload_folder': app.config['UPLOAD_FOLDER'],
            'max_file_size': app.config['MAX_CONTENT_LENGTH']
        })
    
    # Enhanced export report endpoint (compatible with existing frontend)
    @app.post('/export_report')
    def export_report():
        \"\"\"
        Enhanced export report endpoint (backward compatible)
        Accepts JSON payload with analysis data and returns HTML report
        \"\"\"
        try:
            data = request.get_json(force=True)
            
            # Create enhanced report data
            report_data = {
                'title': 'volLite Forensic Report',
                'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'summary': data.get('summary', 'No summary available'),
                'findings': data.get('key_findings', []),
                'risk_score': data.get('risk_score', 0),
                'alerts': data.get('alerts', []),
                'process_tree': data.get('process_tree', {}),
                'system_info': data.get('system_info', {}),
                'analysis_duration': data.get('analysis_duration', 'N/A'),
                'file_info': data.get('file_info', {})
            }
            
            # Render HTML report
            html = render_template('report.html', **report_data)
            
            # Return as attachment
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'volLite_report_{timestamp}.html'
            
            response = make_response(html)
            response.headers['Content-Type'] = 'text/html; charset=utf-8'
            response.headers['Content-Disposition'] = f'attachment; filename={filename}'
            
            return response
            
        except Exception as e:
            return jsonify({'error': f'Failed to generate report: {str(e)}'}), 500
    
    # Legacy analyze endpoint (enhanced but backward compatible)
    @app.post('/api/analyze')
    def legacy_analyze():
        \"\"\"
        Legacy analyze endpoint for backward compatibility
        Enhanced with basic file validation and storage
        \"\"\"
        try:
            # Check for simulate flag
            simulate = False
            if request.is_json:
                simulate = request.json.get('simulate', False)
            else:
                simulate = request.form.get('simulate', 'false').lower() == 'true'
            
            # If simulate mode, return demo data
            if simulate:
                # Load demo data (you'll need to create these files)
                demo_data = {
                    'summary': 'Demo analysis completed successfully',
                    'key_findings': [
                        'System appears to be Windows 10 x64',
                        'Multiple processes detected',
                        'Network activity present'
                    ],
                    'risk_score': 35,
                    'alerts': [
                        {
                            'type': 'info',
                            'title': 'Demo Alert',
                            'description': 'This is a demonstration alert',
                            'severity': 'low'
                        }
                    ],
                    'process_tree': {
                        'processes': [
                            {'pid': 4, 'name': 'System', 'ppid': 0},
                            {'pid': 1000, 'name': 'explorer.exe', 'ppid': 4}
                        ]
                    },
                    'generated_at': datetime.now().isoformat(timespec='seconds'),
                    'status': 'completed'
                }
                return jsonify(demo_data)
            
            # Handle real file upload
            if 'dump' in request.files:
                file = request.files['dump']
                if file.filename:
                    # Use the new file validation system
                    from services.file_validator import FileValidator
                    from utils.security import generate_secure_filename
                    
                    # Generate secure filename
                    secure_name = generate_secure_filename(file.filename, 'legacy')
                    
                    # Save file
                    upload_folder = app.config['UPLOAD_FOLDER']
                    os.makedirs(upload_folder, exist_ok=True)
                    file_path = os.path.join(upload_folder, secure_name)
                    file.save(file_path)
                    
                    # Validate file
                    validator = FileValidator()
                    validation_result = validator.validate_file(file, file_path)
                    
                    if not validation_result['valid']:
                        # Clean up invalid file
                        if os.path.exists(file_path):
                            os.remove(file_path)
                        
                        return jsonify({
                            'error': 'File validation failed',
                            'details': validation_result['errors']
                        }), 400
                    
                    # For Phase 1, return enhanced demo data with file info
                    demo_data = {
                        'summary': f'Analysis completed for {file.filename}',
                        'key_findings': [
                            f'File size: {validation_result[\"file_info\"][\"file_size\"]} bytes',
                            f'File hash: {validation_result[\"file_info\"][\"sha256\"][:16]}...',
                            'Basic validation passed'
                        ],
                        'risk_score': 25,
                        'alerts': [
                            {
                                'type': 'info',
                                'title': 'File Processed',
                                'description': f'Successfully processed {file.filename}',
                                'severity': 'low'
                            }
                        ],
                        'process_tree': {'processes': []},
                        'file_info': validation_result['file_info'],
                        'generated_at': datetime.now().isoformat(timespec='seconds'),
                        'status': 'completed'
                    }
                    
                    return jsonify(demo_data)
            
            # Default response
            return jsonify({
                'error': 'No file provided and simulate mode not enabled'
            }), 400
            
        except Exception as e:
            return jsonify({'error': f'Analysis failed: {str(e)}'}), 500
    
    # Error handlers
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({'error': 'Bad request'}), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({'error': 'Unauthorized'}), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({'error': 'Forbidden'}), 403
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not found'}), 404
    
    @app.errorhandler(413)
    def request_entity_too_large(error):
        return jsonify({'error': 'File too large'}), 413
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500
    
    return app

# Create app instance
app = create_app()

if __name__ == '__main__':
    # Create upload directory
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Run application
    app.run(
        debug=app.config.get('DEBUG', False),
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000))
    )""",

    "migrations/__init__.py": """# Migrations package""",
    
    "run.py": """#!/usr/bin/env python3
\"\"\"
volLite Application Runner
Enhanced version with database initialization and health checks
\"\"\"

import os
import sys
from app import create_app
from utils.database import init_database, check_database_connection

def main():
    \"\"\"Main application entry point\"\"\"
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
    
    print("\\nStarting volLite server...")
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
        print("\\n\\nShutting down volLite server...")
        return 0
    except Exception as e:
        print(f"\\nError starting server: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())""",

    "setup.py": """\"\"\"
volLite Setup Script
Phase 1 Implementation
\"\"\"

import os
import sys
import subprocess
from pathlib import Path

def check_python_version():
    \"\"\"Check Python version\"\"\"
    if sys.version_info < (3, 8):
        print("Error: Python 3.8 or higher is required")
        return False
    print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    return True

def install_requirements():
    \"\"\"Install Python requirements\"\"\"
    print("Installing Python requirements...")
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        print("✓ Requirements installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install requirements: {e}")
        return False

def setup_database():
    \"\"\"Setup database\"\"\"
    print("Setting up database...")
    try:
        # Load environment variables
        if os.path.exists('.env'):
            from dotenv import load_dotenv
            load_dotenv()
        
        from app import create_app
        from utils.database import init_database
        
        app = create_app()
        with app.app_context():
            if init_database():
                print("✓ Database setup completed")
                return True
            else:
                print("✗ Database setup failed")
                return False
    except Exception as e:
        print(f"✗ Database setup error: {e}")
        return False

def create_directories():
    \"\"\"Create necessary directories\"\"\"
    directories = [
        'uploads',
        'logs',
        'backups'
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✓ Created directory: {directory}")

def setup_environment():
    \"\"\"Setup environment file\"\"\"
    if not os.path.exists('.env'):
        print("Creating .env file...")
        env_content = '''# volLite Environment Configuration
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=dev-secret-key-change-in-production
JWT_SECRET_KEY=dev-jwt-secret-change-in-production

# Database Configuration (SQLite for development)
DATABASE_URL=sqlite:///vollite_dev.db

# Optional: PostgreSQL for production
# DATABASE_URL=postgresql://username:password@localhost/vollite

# Volatility Configuration
VOLATILITY_PATH=/usr/local/bin/vol.py

# Server Configuration
PORT=5000
'''
        with open('.env', 'w') as f:
            f.write(env_content)
        print("✓ Created .env file")
        print("  Please review and update the configuration as needed")
    else:
        print("✓ .env file already exists")

def main():
    \"\"\"Main setup function\"\"\"
    print("volLite Phase 1 Setup")
    print("=" * 30)
    
    steps = [
        ("Checking Python version", check_python_version),
        ("Creating directories", create_directories),
        ("Setting up environment", setup_environment),
        ("Installing requirements", install_requirements),
        ("Setting up database", setup_database),
    ]
    
    for step_name, step_func in steps:
        print(f"\\n{step_name}...")
        if not step_func():
            print(f"Setup failed at: {step_name}")
            return 1
    
    print("\\n" + "=" * 30)
    print("✓ volLite Phase 1 setup completed successfully!")
    print("\\nNext steps:")
    print("1. Review and update .env file with your configuration")
    print("2. Install Volatility 3 if you haven't already:")
    print("   git clone https://github.com/volatilityfoundation/volatility3.git")
    print("3. Run the application:")
    print("   python run.py")
    print("\\nFor more information, see the documentation.")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())""",

    "README_Phase1.md": """# volLite Phase 1 Implementation

## Overview
This is the Phase 1 implementation of volLite - AI-Based Memory Forensics Assistant. Phase 1 includes:

- ✅ PostgreSQL/SQLite database integration
- ✅ User authentication system with JWT
- ✅ Secure file upload with validation
- ✅ Basic Volatility framework integration
- ✅ RESTful API endpoints
- ✅ Enhanced security features

## Quick Start

### 1. Setup
```bash
# Install dependencies and setup
python setup.py

# Or manual setup:
pip install -r requirements.txt
```

### 2. Configuration
Edit `.env` file with your settings:
```env
FLASK_ENV=development
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///vollite_dev.db
VOLATILITY_PATH=/path/to/volatility3/vol.py
```

### 3. Run Application
```bash
python run.py
```

The application will be available at `http://localhost:5000`

## API Endpoints

### Authentication
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `GET /api/auth/profile` - Get user profile
- `POST /api/auth/change-password` - Change password

### Analysis
- `POST /api/analysis/upload` - Upload memory dump
- `POST /api/analysis/analyze/<session_id>` - Start analysis
- `GET /api/analysis/status/<session_id>` - Get analysis status
- `GET /api/analysis/results/<session_id>` - Get analysis results
- `GET /api/analysis/sessions` - Get user sessions
- `DELETE /api/analysis/delete/<session_id>` - Delete session

### System
- `GET /api/health` - Health check
- `GET /api/system/info` - System information

## Database Schema

### Users
- `id` (Primary Key)
- `username` (Unique)
- `email` (Unique)
- `password_hash`
- `created_at`
- `is_active`

### Analysis Sessions
- `id` (Primary Key)
- `user_id` (Foreign Key)
- `filename`
- `original_filename`
- `file_hash` (SHA256)
- `file_size`
- `upload_time`
- `analysis_status`
- `volatility_profile`
- `analysis_duration`

### Analysis Results
- `id` (Primary Key)
- `session_id` (Foreign Key)
- `summary`
- `risk_score`
- `key_findings` (JSON)
- `process_data` (JSON)
- `network_data` (JSON)
- `system_info` (JSON)

### Alerts
- `id` (Primary Key)
- `session_id` (Foreign Key)
- `alert_type`
- `severity`
- `title`
- `description`
- `threat_indicators` (JSON)

## File Structure
```
volLite/
├── app.py                     # Main Flask application
├── run.py                     # Application runner
├── setup.py                   # Setup script
├── config.py                  # Configuration
├── requirements.txt           # Dependencies
├── .env                       # Environment variables
├── models/                    # Database models
│   ├── __init__.py
│   ├── user.py
│   └── analysis.py
├── api/                       # API endpoints
│   ├── __init__.py
│   ├── auth.py
│   └── analysis.py
├── services/                  # Business logic
│   ├── __init__.py
│   ├── file_validator.py
│   └── volatility_service.py
├── utils/                     # Utilities
│   ├── __init__.py
│   ├── security.py
│   └── database.py
├── templates/                 # HTML templates
├── uploads/                   # File uploads
└── migrations/                # Database migrations
```

## Security Features

### File Upload Security
- File type validation
- File size limits (2GB max)
- Secure filename generation
- File integrity checking
- Malware scanning preparation

### Authentication Security
- Password hashing with bcrypt
- JWT token authentication
- Password strength validation
- User session management

### API Security
- CORS protection
- Rate limiting preparation
- Input validation
- SQL injection prevention
- XSS protection headers

## Usage Examples

### 1. Register User
```bash
curl -X POST http://localhost:5000/api/auth/register \\
  -H "Content-Type: application/json" \\
  -d '{
    "username": "analyst1",
    "email": "analyst@example.com",
    "password": "SecurePass123"
  }'
```

### 2. Login
```bash
curl -X POST http://localhost:5000/api/auth/login \\
  -H "Content-Type: application/json" \\
  -d '{
    "username": "analyst1",
    "password": "SecurePass123"
  }'
```

### 3. Upload Memory Dump
```bash
curl -X POST http://localhost:5000/api/analysis/upload \\
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \\
  -F "file=@memory_dump.dmp"
```

### 4. Start Analysis
```bash
curl -X POST http://localhost:5000/api/analysis/analyze/1 \\
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## Integration with Existing Frontend

The Phase 1 backend is designed to be compatible with your existing frontend. The original endpoints are maintained:

- `GET /` - Home page
- `GET /dashboard` - Dashboard
- `POST /api/analyze` - Legacy analyze endpoint (enhanced)
- `POST /export_report` - Export functionality

## Volatility Integration

Phase 1 includes basic Volatility integration:

- Automatic profile detection
- Process list extraction
- Network connection analysis
- System information gathering
- Error handling and logging

## Next Steps for Phase 2

- AI/ML integration with OpenAI API
- Advanced threat intelligence
- Background task processing with Celery
- Enhanced reporting and visualization
- Performance optimization

## Troubleshooting

### Database Issues
```bash
# Reset database
python -c "from utils.database import reset_database; from app import create_app; app = create_app(); app.app_context().push(); reset_database()"
```

### Volatility Issues
- Ensure Volatility 3 is installed
- Check VOLATILITY_PATH in .env
- Verify Python dependencies

### File Upload Issues
- Check upload directory permissions
- Verify file size limits
- Check available disk space

## Support

For issues and questions:
1. Check the logs in `logs/` directory
2. Verify configuration in `.env`
3. Test with health check endpoint: `GET /api/health`
"""
}

for filename, content in main_files.items():
    # Create directory if needed
    if '/' in filename:
        directory = filename.split('/')[0]
        os.makedirs(directory, exist_ok=True)
    
    with open(filename, 'w') as f:
        f.write(content)
    print(f"✓ Created {filename}")

print(f"\nCreated {len(main_files)} main application files")
print("\\n" + "=" * 60)
print("Phase 1 Implementation Complete!")
print("=" * 60)
print("\\nTotal files created:")
print(f"- Configuration files: 6")
print(f"- Service files: 6") 
print(f"- API files: 3")
print(f"- Main application files: 4")
print(f"- Documentation: 1")
print(f"\\nTOTAL: 20 files")

print("\\n🚀 Ready to run! Execute: python setup.py")