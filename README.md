# 🔍 volLite - AI-Based Memory Forensics Assistant

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/flask-3.0.0-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/license-MIT-orange.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.0.0--phase1-blue.svg)](https://github.com/danish6904/Vollite)

A Flask-based web application for forensic memory dump analysis, providing automated threat detection and security assessment using Volatility 3 framework.

![volLite Dashboard](https://via.placeholder.com/800x400?text=volLite+Memory+Forensics+Dashboard)

## 📋 Overview

**volLite** is a forensic analysis tool that analyzes memory dump files to detect security threats, malware, and suspicious activities. It combines the power of Volatility 3 with an intuitive web interface for comprehensive memory forensics.

### ✨ Key Features

- 📤 **Memory Dump Upload** - Supports `.dmp`, `.mem`, `.raw`, `.vmem` files (up to 100MB)
- 🔍 **Automated Analysis** - Powered by Volatility 3 framework
- ⚠️ **Threat Detection** - Real-time security alerts and risk scoring
- 📊 **Risk Assessment** - Automated threat scoring (0-100 scale)
- 🌳 **Process Visualization** - Interactive process tree analysis
- 📄 **Report Generation** - Export detailed HTML forensic reports
- 🔐 **Secure** - JWT authentication, file validation, and security headers
- 🎯 **REST API** - Full API for programmatic access

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- PostgreSQL database
- Git

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/danish6904/Vollite.git
cd Vollite/vollite-frontend
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

4. **Configure environment**

Copy the example environment file:
```bash
cp .env.example .env
```

Edit `.env` with your settings:
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
│
├── api/                        # REST API endpoints
│   ├── auth.py                 # Authentication
│   ├── analysis.py             # Analysis endpoints
│   └── enhanced_analysis_endpoints.py
│
├── models/                     # Database models
│   ├── user.py                 # User model
│   └── analysis.py             # Analysis models
│
├── services/                   # Business logic
│   ├── volatility_service.py   # Volatility integration
│   ├── file_validator.py       # File validation
│   └── risk_analyzer.py        # Risk assessment
│
├── templates/                  # HTML templates
├── static/                     # CSS, JS, media files
└── utils/                      # Utility functions
```

## 🔧 Configuration

### Database Setup

```sql
CREATE DATABASE vollite_db;
CREATE USER vollite_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE vollite_db TO vollite_user;
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Flask secret key | Required |
| `JWT_SECRET_KEY` | JWT signing key | Same as SECRET_KEY |
| `DATABASE_URL` | PostgreSQL connection | `postgresql://...` |
| `DEBUG` | Debug mode | `False` |
| `PORT` | Server port | `5000` |

## 📡 API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login and get JWT token

### Analysis
- `POST /api/analyze` - Upload and analyze memory dump
- `GET /api/analysis/:id` - Get analysis results
- `POST /export_report` - Export analysis report

### System
- `GET /api/health` - Health check
- `GET /api/system/info` - System information

## 🧪 Usage Example

### Upload Memory Dump

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
| **Frontend** | HTML5, CSS3, JavaScript |
| **Security** | Flask-CORS, Bcrypt |

## 📊 Current Status: Phase 1

- ✅ File upload and validation
- ✅ Database schema
- ✅ Frontend UI with dashboard
- ✅ Demo/simulation mode
- ✅ Report generation
- 🔄 Full Volatility integration (in progress)
- 🔄 AI-based threat detection (planned)

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 🔒 Security

**Important Security Notes:**
- Never commit `.env` files or credentials
- Change default secret keys in production
- Use strong database passwords
- Keep dependencies updated
- Implement rate limiting for production

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📧 Contact

**Developer:** danish6904  
**Repository:** [https://github.com/danish6904/Vollite](https://github.com/danish6904/Vollite)  
**Issues:** [https://github.com/danish6904/Vollite/issues](https://github.com/danish6904/Vollite/issues)

## 🙏 Acknowledgments

- [Volatility Foundation](https://www.volatilityfoundation.org/) - Memory forensics framework
- Flask community for excellent documentation
- All contributors and testers

---

**⚠️ Disclaimer**: This tool is intended for legitimate forensic analysis and security research only. Users are responsible for complying with applicable laws and regulations.

## 🗺️ Roadmap

- [ ] Complete Volatility 3 integration
- [ ] AI-powered threat detection
- [ ] Real-time analysis monitoring
- [ ] Multi-user support
- [ ] Advanced reporting features
- [ ] Docker deployment support
- [ ] CI/CD pipeline setup
