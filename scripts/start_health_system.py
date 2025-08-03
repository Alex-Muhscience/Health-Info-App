#!/usr/bin/env python3
"""
Complete Health Management System Startup Script
Starts Django frontend and Flask backend with proper initialization
"""

import os
import sys
import subprocess
import time
import threading
import webbrowser
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def print_banner():
    """Print system banner"""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                 HEALTH MANAGEMENT SYSTEM                     ║
    ║                   Production Ready v1.0                     ║
    ║                                                              ║
    ║  🏥 Complete Healthcare Management Solution                  ║
    ║  🔧 Django Frontend + Flask Backend Architecture            ║
    ║  🔒 Production-Ready Security & Authentication               ║
    ║  📊 Real-time Dashboard & Analytics                         ║
    ║  👥 Client Management & Medical Records                     ║
    ║  📅 Appointment Scheduling & Visit Tracking                 ║
    ║  🏥 Health Programs & Treatment Plans                       ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def check_dependencies():
    """Check if all required dependencies are installed"""
    print("🔍 Checking dependencies...")
    
    try:
        # Check Flask dependencies
        import flask
        import flask_sqlalchemy
        import flask_jwt_extended
        print("✅ Flask dependencies OK")
        
        # Check Django dependencies
        import django
        import rest_framework
        print("✅ Django dependencies OK")
        
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("📦 Installing missing dependencies...")
        return install_dependencies()

def install_dependencies():
    """Install missing dependencies"""
    try:
        # Install Flask backend dependencies
        subprocess.run([
            sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'
        ], check=True, cwd=project_root)
        
        # Install Django frontend dependencies
        subprocess.run([
            sys.executable, '-m', 'pip', 'install', '-r', 'django_requirements.txt'
        ], check=True, cwd=project_root)
        
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def initialize_backend():
    """Initialize Flask backend with sample data"""
    print("🔄 Initializing Flask backend...")
    
    try:
        subprocess.run([
            sys.executable, 'init_flask_backend.py'
        ], check=True, cwd=project_root)
        print("✅ Flask backend initialized")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Backend initialization failed: {e}")
        return False

def setup_django():
    """Setup Django frontend"""
    print("🔄 Setting up Django frontend...")
    
    django_dir = project_root / 'django_frontend'
    
    try:
        # Create logs directory
        logs_dir = django_dir / 'logs'
        logs_dir.mkdir(exist_ok=True)
        
        # Create static directory
        static_dir = django_dir / 'static'
        static_dir.mkdir(exist_ok=True)
        
        # Run Django migrations
        subprocess.run([
            sys.executable, 'manage.py', 'migrate'
        ], check=True, cwd=django_dir)
        
        print("✅ Django frontend setup completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Django setup failed: {e}")
        return False

def run_flask_backend():
    """Run Flask backend server"""
    print("🚀 Starting Flask Backend on http://127.0.0.1:8000")
    
    # Set environment variables
    env = os.environ.copy()
    env['FLASK_APP'] = 'backend.app'
    env['FLASK_ENV'] = 'development'
    
    try:
        subprocess.run([
            sys.executable, '-m', 'flask', 'run',
            '--host=127.0.0.1',
            '--port=8000'
        ], env=env, cwd=project_root)
    except KeyboardInterrupt:
        print("🛑 Flask backend stopped")

def run_django_frontend():
    """Run Django frontend server"""
    print("🚀 Starting Django Frontend on http://127.0.0.1:8001")
    
    django_dir = project_root / 'django_frontend'
    
    try:
        subprocess.run([
            sys.executable, 'manage.py', 'runserver', '127.0.0.1:8001'
        ], cwd=django_dir)
    except KeyboardInterrupt:
        print("🛑 Django frontend stopped")

def check_server_health():
    """Check if servers are running properly"""
    import requests
    
    print("🔍 Checking server health...")
    
    try:
        # Check Flask backend
        response = requests.get('http://127.0.0.1:8000/health', timeout=5)
        if response.status_code == 200:
            print("✅ Flask backend is healthy")
        else:
            print("⚠️  Flask backend health check failed")
    except requests.exceptions.RequestException:
        print("❌ Flask backend is not responding")
    
    try:
        # Check Django frontend
        response = requests.get('http://127.0.0.1:8001/', timeout=5)
        if response.status_code in [200, 302]:  # 302 is redirect to login
            print("✅ Django frontend is healthy")
        else:
            print("⚠️  Django frontend health check failed")
    except requests.exceptions.RequestException:
        print("❌ Django frontend is not responding")

def open_browser():
    """Open browser to the application"""
    time.sleep(5)  # Wait for servers to start
    print("🌐 Opening browser...")
    try:
        webbrowser.open('http://127.0.0.1:8001')
    except Exception as e:
        print(f"⚠️  Could not open browser: {e}")

def print_usage_info():
    """Print usage information"""
    info = """
    🎯 SYSTEM READY! 

    📍 Access Points:
    ├─ Django Frontend (Main UI): http://127.0.0.1:8001
    ├─ Flask Backend (API):       http://127.0.0.1:8000
    └─ Backend Health Check:      http://127.0.0.1:8000/health

    🔐 Login Credentials:
    ├─ Username: admin
    └─ Password: admin123

    📋 Sample Data Available:
    ├─ 3 Sample Clients (John Doe, Alice Smith, Michael Johnson)
    ├─ 3 Health Programs (Diabetes, Heart Health, Weight Management)
    ├─ 2 Scheduled Appointments
    └─ 2 Visit Records

    🛠️  Features Available:
    ├─ 👥 Client Management (Add, View, Search, Filter)
    ├─ 📅 Appointment Scheduling
    ├─ 🏥 Visit Recording & Medical History
    ├─ 📊 Health Programs & Enrollment
    ├─ 📈 Dashboard with Statistics
    └─ 🔒 Secure Authentication & Authorization

    ⚠️  Press Ctrl+C to stop both servers
    """
    print(info)

def main():
    """Main function"""
    print_banner()
    
    # Check dependencies
    if not check_dependencies():
        print("❌ Dependency check failed. Exiting.")
        return
    
    # Initialize backend
    if not initialize_backend():
        print("❌ Backend initialization failed. Exiting.")
        return
    
    # Setup Django
    if not setup_django():
        print("❌ Django setup failed. Exiting.")
        return
    
    print("\n🎉 Setup completed successfully!")
    print_usage_info()
    
    try:
        # Start Flask backend in a separate thread
        flask_thread = threading.Thread(target=run_flask_backend, daemon=True)
        flask_thread.start()
        
        # Wait for Flask to start
        time.sleep(3)
        
        # Start browser in a separate thread
        browser_thread = threading.Thread(target=open_browser, daemon=True)
        browser_thread.start()
        
        # Wait a bit more for Flask to fully start
        time.sleep(2)
        
        # Check server health
        check_health_thread = threading.Thread(target=check_server_health, daemon=True)
        check_health_thread.start()
        
        # Start Django frontend in the main thread
        run_django_frontend()
        
    except KeyboardInterrupt:
        print("\n🛑 Shutting down Health Management System...")
        print("✅ System stopped successfully")

if __name__ == '__main__':
    main()
