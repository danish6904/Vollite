# volLite Phase 1 Implementation

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
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "analyst1",
    "email": "analyst@example.com",
    "password": "SecurePass123"
  }'
```

### 2. Login
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "analyst1",
    "password": "SecurePass123"
  }'
```

### 3. Upload Memory Dump
```bash
curl -X POST http://localhost:5000/api/analysis/upload \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "file=@memory_dump.dmp"
```

### 4. Start Analysis
```bash
curl -X POST http://localhost:5000/api/analysis/analyze/1 \
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
