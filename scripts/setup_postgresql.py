#!/usr/bin/env python3
"""
PostgreSQL Setup Script for Health App
This script helps set up PostgreSQL database and user for the health application.
"""

import os
import sys
import subprocess
import getpass
from pathlib import Path

def run_psql_command(command, user="postgres", database="postgres", password=None):
    """Run a psql command with proper error handling"""
    psql_path = r"C:\Program Files\PostgreSQL\17\bin\psql.exe"
    
    if not os.path.exists(psql_path):
        print(f"PostgreSQL not found at {psql_path}")
        return False
    
    env = os.environ.copy()
    if password:
        env['PGPASSWORD'] = password
    
    cmd = [
        psql_path,
        "-U", user,
        "-d", database,
        "-c", command
    ]
    
    try:
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ Command executed successfully: {command}")
            return True
        else:
            print(f"✗ Error executing command: {result.stderr}")
            return False
    except Exception as e:
        print(f"✗ Exception occurred: {e}")
        return False

def create_database_and_user():
    """Create database and user for the health app"""
    print("=== PostgreSQL Setup for Health App ===\n")
    
    # Get PostgreSQL superuser password
    postgres_password = getpass.getpass("Enter PostgreSQL 'postgres' user password: ")
    
    # Test connection
    print("Testing PostgreSQL connection...")
    if not run_psql_command("SELECT version();", password=postgres_password):
        print("Failed to connect to PostgreSQL. Please check your password and try again.")
        return False
    
    print("✓ Connected to PostgreSQL successfully!\n")
    
    # Create database user
    print("Creating health_user...")
    health_password = "health_password_123"  # You can change this
    create_user_cmd = f"CREATE USER health_user WITH PASSWORD '{health_password}';"
    
    if run_psql_command(create_user_cmd, password=postgres_password):
        print("✓ User 'health_user' created successfully")
    else:
        print("User might already exist, continuing...")
    
    # Create database
    print("Creating health_system_db database...")
    create_db_cmd = "CREATE DATABASE health_system_db OWNER health_user;"
    
    if run_psql_command(create_db_cmd, password=postgres_password):
        print("✓ Database 'health_system_db' created successfully")
    else:
        print("Database might already exist, continuing...")
    
    # Create test database
    print("Creating test database...")
    create_test_db_cmd = "CREATE DATABASE test_health_system_db OWNER health_user;"
    
    if run_psql_command(create_test_db_cmd, password=postgres_password):
        print("✓ Test database 'test_health_system_db' created successfully")
    else:
        print("Test database might already exist, continuing...")
    
    # Grant privileges
    print("Granting privileges...")
    grant_cmd = "ALTER USER health_user CREATEDB;"
    run_psql_command(grant_cmd, password=postgres_password)
    
    print(f"\n=== Setup Complete! ===")
    print(f"Database: health_system_db")
    print(f"Test Database: test_health_system_db")
    print(f"Username: health_user")
    print(f"Password: {health_password}")
    print(f"\nPostgreSQL URL: postgresql://health_user:{health_password}@localhost:5432/health_system_db")
    
    return True

def update_env_file():
    """Update the .env file with PostgreSQL configuration"""
    env_path = Path(".env")
    
    if not env_path.exists():
        print("No .env file found")
        return False
    
    print("\nUpdating .env file...")
    
    # Read current content
    with open(env_path, 'r') as f:
        content = f.read()
    
    # Replace SQLite URLs with PostgreSQL URLs
    updated_content = content.replace(
        "DATABASE_URL=sqlite:///health_system.db",
        "DATABASE_URL=postgresql://health_user:health_password_123@localhost:5432/health_system_db"
    ).replace(
        "DATABASE_TEST_URL=sqlite:///test_health_system.db",
        "DATABASE_TEST_URL=postgresql://health_user:health_password_123@localhost:5432/test_health_system_db"
    )
    
    # Write back
    with open(env_path, 'w') as f:
        f.write(updated_content)
    
    print("✓ .env file updated with PostgreSQL configuration")
    return True

def check_postgresql_service():
    """Check if PostgreSQL service is running"""
    print("Checking PostgreSQL service status...")
    
    try:
        result = subprocess.run([
            "powershell", "-Command", 
            "Get-Service -Name postgresql-x64-17 | Select-Object Status"
        ], capture_output=True, text=True)
        
        if "Running" in result.stdout:
            print("✓ PostgreSQL service is running")
            return True
        else:
            print("✗ PostgreSQL service is not running")
            print("Please start PostgreSQL service first:")
            print("  sc start postgresql-x64-17")
            return False
    except Exception as e:
        print(f"Error checking service: {e}")
        return False

def main():
    """Main setup function"""
    print("Health App PostgreSQL Setup\n")
    
    # Check if PostgreSQL service is running
    if not check_postgresql_service():
        print("\nTrying to start PostgreSQL service...")
        try:
            subprocess.run(["sc", "start", "postgresql-x64-17"], check=True)
            print("✓ PostgreSQL service started")
        except subprocess.CalledProcessError:
            print("✗ Failed to start PostgreSQL service. Please start it manually.")
            return
    
    # Create database and user
    if create_database_and_user():
        # Ask user if they want to update .env file
        response = input("\nDo you want to update the .env file to use PostgreSQL? (y/n): ")
        if response.lower() == 'y':
            update_env_file()
            print("\n✓ Setup complete! Your app is now configured to use PostgreSQL.")
        else:
            print("\n✓ Database setup complete. You can manually update your .env file when ready.")
    else:
        print("\n✗ Setup failed. Please check the errors above and try again.")

if __name__ == "__main__":
    main()
