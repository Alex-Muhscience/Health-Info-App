#!/usr/bin/env python3
"""
Comprehensive Health Management System Startup Script
Initializes the database and starts both Django frontend and Flask backend
"""

import os
import sys
import subprocess
import time
import threading
from pathlib import Path

def run_command(command, cwd=None, name="Process"):
    """Run a command in a separate thread"""
    def target():
        try:
            print(f"Starting {name}...")
            result = subprocess.run(
                command,
                cwd=cwd,
                shell=True,
                capture_output=False,
                text=True
            )
            if result.returncode != 0:
                print(f"❌ {name} failed with return code {result.returncode}")
            else:
                print(f"✅ {name} completed successfully")
        except Exception as e:
            print(f"❌ Error running {name}: {str(e)}")
    
    thread = threading.Thread(target=target)
    thread.daemon = True
    thread.start()
    return thread

def check_requirements():
    """Check if required packages are installed"""
    required_packages = [
        'flask', 'django', 'sqlalchemy', 'flask-migrate',
        'flask-jwt-extended', 'flask-cors', 'requests',
        'werkzeug', 'marshmallow', 'flask-marshmallow'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Missing required packages:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\nInstall missing packages using:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    return True

def initialize_database():
    """Initialize the comprehensive database"""
    print("🔧 Initializing comprehensive database...")
    
    try:
        # Run the comprehensive database setup
        result = subprocess.run([
            sys.executable, "create_comprehensive_db.py"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Database initialized successfully!")
            print(result.stdout)
            return True
        else:
            print("❌ Database initialization failed!")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error initializing database: {str(e)}")
        return False

def setup_django_database():
    """Setup Django database"""
    print("🔧 Setting up Django database...")
    
    django_dir = Path("django_frontend")
    
    try:
        # Django migrations
        commands = [
            "python manage.py makemigrations",
            "python manage.py migrate"
        ]
        
        for cmd in commands:
            result = subprocess.run(
                cmd.split(),
                cwd=django_dir,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                print(f"❌ Django command failed: {cmd}")
                print(result.stderr)
                return False
        
        print("✅ Django database setup completed!")
        return True
        
    except Exception as e:
        print(f"❌ Error setting up Django database: {str(e)}")
        return False

def main():
    """Main function to start the comprehensive health management system"""
    
    print("🏥 Comprehensive Health Management System")
    print("=" * 50)
    
    # Check requirements
    print("📋 Checking requirements...")
    if not check_requirements():
        return False
    
    print("✅ All requirements satisfied!")
    
    # Initialize databases
    if not initialize_database():
        return False
    
    if not setup_django_database():
        return False
    
    print("\n🚀 Starting Health Management System...")
    print("=" * 50)
    
    # Set environment variables
    os.environ.setdefault('FLASK_ENV', 'development')
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'health_frontend.settings')
    
    # Start Flask backend
    flask_thread = run_command(
        "python -m backend.app",
        name="Flask Backend (Port 8000)"
    )
    
    # Give Flask time to start
    time.sleep(3)
    
    # Start Django frontend
    django_thread = run_command(
        "python manage.py runserver 8001",
        cwd="django_frontend",
        name="Django Frontend (Port 8001)"
    )
    
    print("\n🌐 Application URLs:")
    print("=" * 30)
    print("🔹 Frontend (Django): http://127.0.0.1:8001")
    print("🔹 Backend API (Flask): http://127.0.0.1:8000")
    print("🔹 API Health Check: http://127.0.0.1:8000/health")
    
    print("\n👤 Default Login Credentials:")
    print("=" * 35)
    print("🔸 Admin: admin / admin123")
    print("🔸 Doctor: dr.smith / doctor123") 
    print("🔸 Nurse: nurse.jane / nurse123")
    
    print("\n📊 Available Features:")
    print("=" * 25)
    print("✓ Patient Management")
    print("✓ Appointment Scheduling")
    print("✓ Visit Records")
    print("✓ Staff Management")
    print("✓ Laboratory Management")
    print("✓ Pharmacy & Prescriptions")
    print("✓ Hospital Admissions")
    print("✓ Billing & Insurance")
    print("✓ Medical Records")
    print("✓ Inventory Management")
    
    print("\n⚠️  Press Ctrl+C to stop both services")
    print("=" * 40)
    
    try:
        # Keep the main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down Health Management System...")
        print("👋 Goodbye!")
        return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
