#!/usr/bin/env python3
"""
Health App Startup Script

This script starts both the backend Flask server and frontend Streamlit server concurrently.
"""

import sys
import os
import subprocess
import threading
import time
import signal
import requests
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

def check_port(port, host='127.0.0.1'):
    """Check if a port is available"""
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect((host, port))
            return True
        except ConnectionRefusedError:
            return False
        except Exception:
            return False

def wait_for_backend(max_attempts=30):
    """Wait for backend to be ready"""
    print("⏳ Waiting for backend to start...")
    for i in range(max_attempts):
        try:
            response = requests.get("http://127.0.0.1:8000/health", timeout=2)
            if response.status_code == 200:
                print("✅ Backend is ready!")
                return True
        except:
            pass
        time.sleep(1)
        if i % 5 == 0:
            print(f"   Still waiting... ({i+1}/{max_attempts})")
    
    print("❌ Backend failed to start in time")
    return False

def run_backend():
    """Run the Flask backend server"""
    print("🚀 Starting Backend Server...")
    try:
        env = os.environ.copy()
        env['PYTHONPATH'] = str(Path(__file__).parent)
        
        process = subprocess.Popen([
            sys.executable, "run_backend.py"
        ], cwd=str(Path(__file__).parent), env=env)
        
        return process
    except Exception as e:
        print(f"❌ Failed to start backend: {e}")
        return None

def run_frontend():
    """Run the Streamlit frontend server"""
    print("🖥️  Starting Frontend Server...")
    try:
        frontend_path = Path(__file__).parent / "frontend" / "app.py"
        
        process = subprocess.Popen([
            sys.executable, "-m", "streamlit", "run", str(frontend_path),
            "--server.headless", "false",
            "--server.runOnSave", "true",
            "--browser.gatherUsageStats", "false",
            "--server.port", "8501"
        ], cwd=str(Path(__file__).parent))
        
        return process
    except Exception as e:
        print(f"❌ Failed to start frontend: {e}")
        return None

def cleanup_processes(processes):
    """Clean up running processes"""
    print("\n🛑 Shutting down servers...")
    for process in processes:
        if process and process.poll() is None:
            try:
                process.terminate()
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
    print("👋 All servers stopped")

def main():
    """Main function to orchestrate the startup"""
    print("🏥 Health Management System Startup")
    print("=" * 50)
    
    # Check if ports are already in use
    if check_port(8000):
        print("⚠️  Port 8000 is already in use. Backend may already be running.")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            return
    
    if check_port(8501):
        print("⚠️  Port 8501 is already in use. Frontend may already be running.")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            return
    
    processes = []
    
    try:
        # Start backend
        backend_process = run_backend()
        if backend_process:
            processes.append(backend_process)
        
        # Wait for backend to be ready
        if not wait_for_backend():
            print("❌ Backend startup failed")
            cleanup_processes(processes)
            return
        
        # Start frontend
        frontend_process = run_frontend()
        if frontend_process:
            processes.append(frontend_process)
        
        print("\n🎉 Health App is now running!")
        print("📍 Frontend: http://localhost:8501")
        print("📍 Backend API: http://127.0.0.1:8000")
        print("📍 Health Check: http://127.0.0.1:8000/health")
        print("🔐 Default login: admin / admin123")
        print("\n⏹️  Press Ctrl+C to stop all servers")
        
        # Wait for user to interrupt
        while True:
            time.sleep(1)
            # Check if processes are still running
            active_processes = [p for p in processes if p and p.poll() is None]
            if not active_processes:
                print("All processes have stopped")
                break
                
    except KeyboardInterrupt:
        print("\n🛑 Received shutdown signal...")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    finally:
        cleanup_processes(processes)

if __name__ == "__main__":
    main()
