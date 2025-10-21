"""
volLite Setup Script
Phase 1 Implementation
"""

import os
import sys
import subprocess
from pathlib import Path

def check_python_version():
    """Check Python version"""
    if sys.version_info < (3, 8):
        print("Error: Python 3.8 or higher is required")
        return False
    print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    return True

def install_requirements():
    """Install Python requirements"""
    print("Installing Python requirements...")
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        print("✓ Requirements installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install requirements: {e}")
        return False

def setup_database():
    """Setup database"""
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
    """Create necessary directories"""
    directories = [
        'uploads',
        'logs',
        'backups'
    ]

    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✓ Created directory: {directory}")

def setup_environment():
    """Setup environment file"""
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
    """Main setup function"""
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
        print(f"\n{step_name}...")
        if not step_func():
            print(f"Setup failed at: {step_name}")
            return 1

    print("\n" + "=" * 30)
    print("✓ volLite Phase 1 setup completed successfully!")
    print("\nNext steps:")
    print("1. Review and update .env file with your configuration")
    print("2. Install Volatility 3 if you haven't already:")
    print("   git clone https://github.com/volatilityfoundation/volatility3.git")
    print("3. Run the application:")
    print("   python run.py")
    print("\nFor more information, see the documentation.")

    return 0

if __name__ == '__main__':
    sys.exit(main())