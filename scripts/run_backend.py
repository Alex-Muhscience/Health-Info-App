#!/usr/bin/env python3
import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend import create_app, db

def init_database():
    """Initialize the database with tables and default data"""
    try:
        from backend.init_db import init_db
        print("🔄 Initializing database...")
        init_db()
        print("✅ Database initialized successfully!")
    except Exception as e:
        print(f"❌ Database initialization failed: {str(e)}")
        return False
    return True

def main():
    """Main function to run the backend server"""
    print("🚀 Starting Health App Backend Server...")
    
    # Initialize database if needed
    if not init_database():
        return
    
    # Create Flask app
    app = create_app()
    
    with app.app_context():
        # Ensure all tables exist
        db.create_all()
        print("📊 Database tables verified")
    
    print("🏥 Health App Backend is running at http://127.0.0.1:8000")
    print("📖 API Documentation available at http://127.0.0.1:8000/health")
    print("🔒 Default admin credentials: admin/admin123")
    print("⏹️  Press Ctrl+C to stop the server")
    
    # Run the Flask development server
    app.run(
        host="127.0.0.1",
        port=8000,
        debug=True,
        use_reloader=False  # Avoid issues with path changes
    )

if __name__ == "__main__":
    main()
