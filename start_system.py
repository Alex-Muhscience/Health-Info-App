#!/usr/bin/env python3
"""
Health Management System Startup Script
Starts both Flask backend and Django frontend services
"""

import os
import sys
import subprocess
import time
import signal
import platform
from pathlib import Path

def print_banner():
    """Print system banner"""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                 🏥 Health Management System                   ║
    ║                                                              ║
    ║  A comprehensive healthcare management platform              ║
    ║  Flask Backend + Django Frontend + Advanced Analytics       ║
    ║                                                              ║
    ║  Starting services...                                        ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 9):
        print("❌ Error: Python 3.9 or higher is required")
        print(f"Current version: {sys.version}")
        sys.exit(1)
    print(f"✅ Python version: {sys.version.split()[0]}")

def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = ['flask', 'django', 'sqlalchemy', 'requests']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} is installed")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package} is missing")
    
    if missing_packages:
        print(f"\n❌ Missing packages: {', '.join(missing_packages)}")
        print("Please run: pip install -r requirements.txt")
        sys.exit(1)

def setup_environment():
    """Setup environment variables"""
    env_file = Path('.env')
    if not env_file.exists():
        print("⚠️  Warning: .env file not found")
        print("Creating basic .env file...")
        
        env_content = """# Health Management System Configuration
FLASK_ENV=development
DEBUG=True
SECRET_KEY=dev-secret-key-change-in-production
JWT_SECRET_KEY=dev-jwt-secret-change-in-production
DATABASE_URL=sqlite:///dev_health_system.db
CORS_ORIGINS=http://localhost:8001,http://127.0.0.1:8001
FLASK_API_URL=http://127.0.0.1:8000/api
LOG_LEVEL=INFO
"""
        with open('.env', 'w') as f:
            f.write(env_content)
        print("✅ Created .env file with default settings")
    else:
        print("✅ .env file found")

def check_database():
    """Check if database is set up"""
    db_file = Path('backend/dev_health_system.db')
    if not db_file.exists():
        print("⚠️  Database not found, creating sample database...")
        try:
            subprocess.run([sys.executable, 'scripts/create_comprehensive_db.py'], 
                         check=True, capture_output=True)
            print("✅ Database created with sample data")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to create database: {e}")
            print("Please run: python scripts/create_comprehensive_db.py")
            return False
    else:
        print("✅ Database found")
    return True

def start_backend():
    """Start Flask backend"""
    print("\n🚀 Starting Flask Backend (Port 8000)...")
    
    backend_cmd = [sys.executable, 'backend/app.py']
    
    # Set environment variables
    env = os.environ.copy()
    env['FLASK_ENV'] = 'development'
    env['FLASK_DEBUG'] = '1'
    
    try:
        backend_process = subprocess.Popen(
            backend_cmd,
            env=env,
            cwd=os.getcwd(),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        # Wait a moment for the backend to start
        time.sleep(3)
        
        if backend_process.poll() is None:
            print("✅ Flask Backend started successfully")
            return backend_process
        else:
            print("❌ Flask Backend failed to start")
            output, _ = backend_process.communicate()
            print(f"Error output: {output}")
            return None
            
    except Exception as e:
        print(f"❌ Failed to start Flask Backend: {e}")
        return None

def start_frontend():
    """Start Django frontend"""
    print("\n🚀 Starting Django Frontend (Port 8001)...")
    
    frontend_cmd = [sys.executable, 'manage.py', 'runserver', '8001']
    
    try:
        frontend_process = subprocess.Popen(
            frontend_cmd,
            cwd='django_frontend',
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        # Wait a moment for the frontend to start
        time.sleep(3)
        
        if frontend_process.poll() is None:
            print("✅ Django Frontend started successfully")
            return frontend_process
        else:
            print("❌ Django Frontend failed to start")
            output, _ = frontend_process.communicate()
            print(f"Error output: {output}")
            return None
            
    except Exception as e:
        print(f"❌ Failed to start Django Frontend: {e}")
        return None

def print_success_message():
    """Print success message with access URLs"""
    success_msg = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                    🎉 System Started Successfully!           ║
    ║                                                              ║
    ║  🌐 Frontend (Django): http://localhost:8001                 ║
    ║  🔧 Backend (Flask):   http://localhost:8000                 ║
    ║  📚 API Docs:          http://localhost:8000/api/docs        ║
    ║                                                              ║
    ║  👤 Default Login Credentials:                               ║
    ║  • Admin: admin / admin123                                   ║
    ║  • Doctor: dr.smith / doctor123                              ║
    ║  • Nurse: nurse.jane / nurse123                              ║
    ║                                                              ║
    ║  Press Ctrl+C to stop all services                          ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(success_msg)

def cleanup_processes(processes):
    """Clean up running processes"""
    print("\n🔄 Shutting down services...")
    
    for process in processes:
        if process and process.poll() is None:
            try:
                if platform.system() == "Windows":
                    process.terminate()
                else:
                    process.send_signal(signal.SIGTERM)
                
                # Wait for graceful shutdown
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
                    
            except Exception as e:
                print(f"Error stopping process: {e}")
    
    print("✅ All services stopped")

def main():
    """Main startup function"""
    print_banner()
    
    # Pre-flight checks
    check_python_version()
    check_dependencies()
    setup_environment()
    
    if not check_database():
        sys.exit(1)
    
    processes = []
    
    try:
        # Start backend
        backend_process = start_backend()
        if backend_process:
            processes.append(backend_process)
        else:
            print("❌ Failed to start backend, exiting...")
            sys.exit(1)
        
        # Start frontend
        frontend_process = start_frontend()
        if frontend_process:
            processes.append(frontend_process)
        else:
            print("❌ Failed to start frontend, stopping backend...")
            cleanup_processes(processes)
            sys.exit(1)
        
        # Print success and wait
        print_success_message()
        
        # Keep the main process alive and monitor services
        try:
            while True:
                time.sleep(1)
                
                # Check if any process has died
                for i, process in enumerate(processes):
                    if process and process.poll() is not None:
                        print(f"❌ Service {i+1} has stopped unexpectedly")
                        cleanup_processes(processes)
                        sys.exit(1)
                        
        except KeyboardInterrupt:
            print("\n⏹️  Received shutdown signal...")
            
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    finally:
        cleanup_processes(processes)

if __name__ == "__main__":
    main()
