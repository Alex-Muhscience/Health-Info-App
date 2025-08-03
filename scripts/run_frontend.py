#!/usr/bin/env python3
import sys
import os
import subprocess

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def check_backend_status():
    """Check if backend is running"""
    import requests
    try:
        response = requests.get("http://127.0.0.1:8000/health", timeout=3)
        return response.status_code == 200
    except:
        return False

def main():
    """Main function to run the frontend server"""
    print("🚀 Starting Health App Frontend...")
    
    # Check if backend is running
    if not check_backend_status():
        print("⚠️  Warning: Backend server is not running at http://127.0.0.1:8000")
        print("   Please start the backend server first using: python run_backend.py")
        print("   Continuing anyway - you can start the backend later.")
        print()
    else:
        print("✅ Backend server is running")
    
    print("🏥 Starting Streamlit Frontend...")
    print("🌐 Frontend will be available at http://localhost:8501")
    print("🔒 Default login: admin/admin123")
    print("⏹️  Press Ctrl+C to stop the server")
    print("-" * 50)
    
    # Run Streamlit
    frontend_path = os.path.join(os.path.dirname(__file__), "frontend", "app.py")
    
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", frontend_path,
            "--server.headless", "false",
            "--server.runOnSave", "true",
            "--browser.gatherUsageStats", "false"
        ], check=True)
    except KeyboardInterrupt:
        print("\n👋 Frontend server stopped")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start frontend: {e}")

if __name__ == "__main__":
    main()
