#!/usr/bin/env python3
"""
Startup script for Health Management System
Runs Django frontend and Flask backend concurrently
"""

import os
import sys
import subprocess
import time
import threading
from pathlib import Path

# Add project root to a Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def run_flask_backend():
    """Run the Flask backend server"""
    print("🔄 Starting Flask Backend...")
    
    # Change to project root directory
    os.chdir(project_root)
    
    # Set environment variables for Flask
    env = os.environ.copy()
    env['FLASK_APP'] = 'backend.app'
    env['FLASK_ENV'] = 'development'
    
    try:
        # Run Flask backend
        subprocess.run([
            sys.executable, '-m', 'flask', 'run',
            '--host=127.0.0.1',
            '--port=8000'
        ], env=env, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Flask backend failed to start: {e}")
    except KeyboardInterrupt:
        print("🛑 Flask backend stopped by user")

def run_django_frontend():
    """Run the Django frontend server"""
    print("🔄 Starting Django Frontend...")
    
    # Change to Django project directory
    django_dir = project_root / 'django_frontend'
    os.chdir(django_dir)
    
    try:
        # Run Django development server
        subprocess.run([
            sys.executable, 'manage.py', 'runserver',
            '127.0.0.1:8001'
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Django frontend failed to start: {e}")
    except KeyboardInterrupt:
        print("🛑 Django frontend stopped by user")

def setup_django():
    """Setup Django (migrations, static files, etc.)"""
    print("🔄 Setting up Django...")
    
    django_dir = project_root / 'django_frontend'
    os.chdir(django_dir)
    
    try:
        # Create logs directory if it doesn't exist
        logs_dir = django_dir / 'logs'
        logs_dir.mkdir(exist_ok=True)
        
        # Create static directory if it doesn't exist
        static_dir = django_dir / 'static'
        static_dir.mkdir(exist_ok=True)
        
        # Run Django migrations
        print("🔄 Running Django migrations...")
        subprocess.run([sys.executable, 'manage.py', 'migrate'], check=True)
        
        # Create superuser if needed (optional)
        print("✅ Django setup completed")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Django setup failed: {e}")
        return False
    
    return True

def setup_flask():
    """Setup Flask (migrations, database initialization)"""
    print("🔄 Setting up Flask...")
    
    os.chdir(project_root)
    
    try:
        # Create logs directory if it doesn't exist
        logs_dir = project_root / 'logs'
        logs_dir.mkdir(exist_ok=True)
        
        # Initialize Flask database migrations if not already done
        from backend.database import db
        from backend import create_app
        
        app = create_app()
        with app.app_context():
            # Create tables
            db.create_all()
            print("✅ Flask database setup completed")
        
    except Exception as e:
        print(f"❌ Flask setup failed: {e}")
        return False
    
    return True

def install_dependencies():
    """Install required dependencies"""
    print("🔄 Installing dependencies...")
    
    # Install main requirements
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], 
                      check=True, cwd=project_root)
        print("✅ Flask dependencies installed")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install Flask dependencies: {e}")
        return False
    
    # Install Django requirements
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'django_requirements.txt'], 
                      check=True, cwd=project_root)
        print("✅ Django dependencies installed")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install Django dependencies: {e}")
        return False
    
    return True

def main():
    """Main function to start both servers"""
    print("🚀 Health Management System Startup")
    print("=" * 50)
    
    # Install dependencies
    if not install_dependencies():
        print("❌ Failed to install dependencies. Exiting.")
        return
    
    # Setup Flask
    if not setup_flask():
        print("❌ Flask setup failed. Exiting.")
        return
    
    # Setup Django
    if not setup_django():
        print("❌ Django setup failed. Exiting.")
        return
    
    print("\n🎉 Setup completed successfully!")
    print("\n🔄 Starting servers...")
    print("📍 Flask Backend will run on: http://127.0.0.1:8000")
    print("📍 Django Frontend will run on: http://127.0.0.1:8001")
    print("\n⚠️  Press Ctrl+C to stop both servers\n")
    
    # Give a moment for the user to read the messages
    time.sleep(2)
    
    try:
        # Start Flask backend in a separate thread
        flask_thread = threading.Thread(target=run_flask_backend, daemon=True)
        flask_thread.start()
        
        # Wait a moment for Flask to start
        time.sleep(3)
        
        # Start Django frontend in the main thread
        run_django_frontend()
        
    except KeyboardInterrupt:
        print("\n🛑 Shutting down servers...")
        print("✅ Health Management System stopped")

if __name__ == '__main__':
    main()
