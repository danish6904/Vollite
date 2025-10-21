# 🔍 volLite - AI-Based Memory Forensics Assistant

A Flask-based web application for forensic memory dump analysis, providing automated threat detection and security assessment.

![Version](https://img.shields.io/badge/version-1.0.0--phase1-blue)
![Python](https://img.shields.io/badge/python-3.8+-green)
![Flask](https://img.shields.io/badge/flask-3.0.0-lightgrey)
![License](https://img.shields.io/badge/license-MIT-orange)

## 📋 Overview

**volLite** is a forensic analysis tool that analyzes memory dump files using Volatility 3 framework. It provides:
- 📤 Memory dump file upload and validation
- 🔍 Automated forensic analysis
- ⚠️ Security threat detection and alerts
- 📊 Risk scoring and assessment
- 📄 HTML report generation
- 🌳 Process tree visualization

## ✨ Features

### Core Capabilities
- **File Upload & Validation**: Accepts `.dmp`, `.mem`, `.raw`, `.vmem` files (up to 100MB)
- **Volatility 3 Integration**: Leverages industry-standard memory forensics framework
- **Risk Assessment**: Automated threat scoring (0-100 scale)
- **Security Alerts**: Real-time detection of suspicious processes and artifacts
- **Report Export**: Generate downloadable HTML forensic reports
- **RESTful API**: Full API for programmatic access

### Security Features
- 🔐 JWT-based authentication
- 🛡️ Security headers middleware
- 🔒 File validation and sanitization
- 🔑 SHA-256 hash verification
- 🚫 CORS protection

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- PostgreSQL database
- Git

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/YOUR_USERNAME/vollite-frontend.git
cd vollite-frontend
```

2. **Create virtual environment**
```bash
# Windows PowerShell
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# macOS/Linux
python3 -m venv .venv
source .venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**

Create a `.env` file in the project root:
```env
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-here
DATABASE_URL=postgresql://user:password@localhost:5432/vollite_db
DEBUG=False
```

5. **Initialize database**
```bash
python
>>> from app import app, db
>>> with app.app_context():
...     db.create_all()
>>> exit()
```

6. **Run the application**
```bash
python app.py
```

7. **Access the application**
Open your browser to `http://localhost:5000`

## 📁 Project Structure

```
vollite-frontend/
├── app.py                      # Main application entry point
├── config.py                   # Configuration settings
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables (not in repo)
├── .gitignore                  # Git ignore rules
│
├── api/                        # REST API endpoints
│   ├── __init__.py
│   ├── auth.py                 # Authentication endpoints
│   ├── analysis.py             # Analysis endpoints
│   └── enhanced_analysis_endpoints.py
│
├── models/                     # Database models
│   ├── __init__.py
│   ├── user.py                 # User model
│   └── analysis.py             # Analysis session models
│
├── services/                   # Business logic
│   ├── __init__.py
│   ├── volatility_service.py   # Volatility 3 interface
│   ├── file_validator.py       # File validation service
│   └── risk_analyzer.py        # Risk assessment engine
│
├── templates/                  # HTML templates
│   ├── base.html
│   ├── home.html
│   ├── dashboard.html
│   ├── report.html
│   └── ...
│
├── static/                     # Static assets
│   ├── css/
│   ├── js/
│   └── videos/
│
├── utils/                      # Utility functions
│   ├── database.py
│   └── security.py
│
├── uploads/                    # Upload directory (not in repo)
└── logs/                       # Application logs (not in repo)
```

## 🔧 Configuration

### Database Setup

Create PostgreSQL database:
```sql
CREATE DATABASE vollite_db;
CREATE USER vollite_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE vollite_db TO vollite_user;
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Flask secret key | `dev-secret-key-change-in-production` |
| `JWT_SECRET_KEY` | JWT signing key | Same as SECRET_KEY |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://postgres:password@localhost:5432/vollite_db` |
| `DEBUG` | Debug mode | `False` |
| `PORT` | Server port | `5000` |

## 📡 API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login and get JWT token

### Analysis
- `POST /api/analyze` - Upload and analyze memory dump
- `GET /api/analysis/:id` - Get analysis results
- `POST /export_report` - Export analysis report as HTML

### System
- `GET /api/health` - Health check endpoint
- `GET /api/system/info` - System information

## 🧪 Usage Example

### Upload and Analyze Memory Dump

```bash
curl -X POST http://localhost:5000/api/analyze \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "dump=@memory_dump.dmp"
```

### Simulate Analysis (Demo Mode)

```bash
curl -X POST http://localhost:5000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"simulate": true}'
```

## 🛠️ Technology Stack

| Component | Technology |
|-----------|-----------|
| **Backend** | Flask 3.0.0 |
| **Database** | PostgreSQL + SQLAlchemy |
| **Authentication** | JWT (Flask-JWT-Extended) |
| **Forensics** | Volatility 3 (v2.5.0) |
| **File Validation** | python-magic |
| **Frontend** | HTML5, CSS3, JavaScript |
| **Security** | Flask-CORS, Bcrypt |

## 📊 Current Status: Phase 1

- ✅ Basic file upload and validation
- ✅ Database schema and models
- ✅ Frontend UI with dashboard
- ✅ Demo/simulation mode
- ✅ Report generation
- 🔄 Full Volatility analysis integration (in progress)
- 🔄 AI-based threat detection (planned)

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🔒 Security

**Important Security Notes:**
- Never commit `.env` files or sensitive credentials
- Change default secret keys in production
- Use strong passwords for database
- Keep dependencies updated
- Validate all file uploads
- Implement rate limiting for production

## 📧 Contact

For questions or support, please open an issue on GitHub.

## 🙏 Acknowledgments

- [Volatility Foundation](https://www.volatilityfoundation.org/) - Memory forensics framework
- Flask community for excellent documentation
- All contributors and testers

---

**⚠️ Disclaimer**: This tool is intended for legitimate forensic analysis and security research only. Users are responsible for complying with applicable laws and regulations.
