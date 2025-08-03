#!/usr/bin/env python3
"""
Admin User Creation Script
This script creates the admin user and initializes the database for the Health App.
"""

import sys
import os
from pathlib import Path

# Add the backend directory to the Python path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from werkzeug.security import generate_password_hash
from backend import create_app, db
from backend.models import User
from backend.config import Config
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_admin_user():
    """Create the admin user"""
    app = create_app()
    
    with app.app_context():
        try:
            # Create tables if they don't exist
            db.create_all()
            
            # Check if admin already exists
            existing_admin = User.query.filter_by(username='admin').first()
            if existing_admin:
                logger.info("Admin user already exists")
                logger.info(f"Admin username: {existing_admin.username}")
                logger.info(f"Admin email: {existing_admin.email}")
                logger.info(f"Admin role: {existing_admin.role}")
                logger.info(f"Admin is_active: {existing_admin.is_active}")
                return existing_admin
            
            # Get admin details from environment or use defaults
            admin_username = os.getenv('DEFAULT_ADMIN_USERNAME', 'admin')
            admin_email = os.getenv('DEFAULT_ADMIN_EMAIL', 'admin@healthsystem.org')
            admin_password = os.getenv('DEFAULT_ADMIN_PASSWORD', 'admin123')
            
            logger.info(f"Creating admin user: {admin_username}")
            
            # Hash the password
            hashed_password = generate_password_hash(
                admin_password,
                method='pbkdf2:sha256',
                salt_length=32
            )
            
            # Create admin user
            admin_user = User(
                username=admin_username,
                email=admin_email,
                password=hashed_password,
                role='admin',
                is_active=True
            )
            
            db.session.add(admin_user)
            db.session.commit()
            
            logger.info("✅ Admin user created successfully!")
            logger.info(f"Username: {admin_username}")
            logger.info(f"Email: {admin_email}")
            logger.info(f"Password: {admin_password}")
            logger.info(f"Role: admin")
            
            return admin_user
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Error creating admin user: {str(e)}")
            raise


def verify_admin_login():
    """Verify that admin can login"""
    app = create_app()
    
    with app.app_context():
        try:
            from werkzeug.security import check_password_hash
            
            admin_username = os.getenv('DEFAULT_ADMIN_USERNAME', 'admin')
            admin_password = os.getenv('DEFAULT_ADMIN_PASSWORD', 'admin123')
            
            user = User.query.filter_by(username=admin_username).first()
            
            if not user:
                logger.error("❌ Admin user not found")
                return False
                
            if not user.is_active:
                logger.error("❌ Admin user is not active")
                return False
                
            if not check_password_hash(user.password, admin_password):
                logger.error("❌ Admin password verification failed")
                return False
                
            logger.info("✅ Admin login verification successful")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error verifying admin login: {str(e)}")
            return False


def main():
    """Main function"""
    print("Health App Admin Setup")
    print("=" * 50)
    
    try:
        # Create admin user
        admin_user = create_admin_user()
        
        # Verify login
        if verify_admin_login():
            print("\n✅ Setup completed successfully!")
            print("\nYou can now login with:")
            print(f"Username: admin")
            print(f"Password: admin123")
            print(f"Role: admin")
            print("\n🚨 IMPORTANT: Change the admin password after first login!")
        else:
            print("\n❌ Setup completed but login verification failed")
            
    except Exception as e:
        print(f"\n❌ Setup failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
