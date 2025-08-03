"""
Production Database Configuration and Management
"""

import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy import event, text
from sqlalchemy.engine import Engine
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()


class DatabaseConfig:
    """Production database configuration management"""
    
    @staticmethod
    def get_database_url(environment: str = None) -> str:
        """Get database URL based on environment"""
        environment = environment or os.getenv('FLASK_ENV', 'production')
        
        if environment == 'testing':
            return os.getenv('DATABASE_TEST_URL', 'sqlite:///test_health_system.db')
        elif environment == 'development':
            return os.getenv('DATABASE_DEV_URL', 'sqlite:///dev_health_system.db')
        else:  # production
            db_url = os.getenv('DATABASE_URL')
            if not db_url:
                raise ValueError("DATABASE_URL must be set for production environment")
            
            # Handle PostgreSQL URL formatting for different providers
            if db_url.startswith('postgres://'):
                db_url = db_url.replace('postgres://', 'postgresql://', 1)
            
            return db_url
    
    @staticmethod
    def get_engine_options(environment: str = None) -> Dict[str, Any]:
        """Get SQLAlchemy engine options for production"""
        environment = environment or os.getenv('FLASK_ENV', 'production')
        
        base_options = {
            'pool_pre_ping': True,
            'pool_recycle': int(os.getenv('DB_POOL_RECYCLE', '3600')),
            'echo': os.getenv('SQL_ECHO', 'false').lower() == 'true'
        }
        
        if environment == 'production':
            # Production-optimized settings
            base_options.update({
                'pool_size': int(os.getenv('DB_POOL_SIZE', '20')),
                'max_overflow': int(os.getenv('DB_MAX_OVERFLOW', '30')),
                'pool_timeout': int(os.getenv('DB_POOL_TIMEOUT', '30')),
                'echo': False,  # Never echo SQL in production
                'connect_args': {
                    'connect_timeout': 10,
                    'application_name': 'health_management_system'
                }
            })
        elif environment == 'development':
            base_options.update({
                'pool_size': 5,
                'max_overflow': 10,
                'echo': os.getenv('SQL_ECHO', 'false').lower() == 'true'
            })
        else:  # testing
            base_options.update({
                'pool_size': 1,
                'max_overflow': 0,
                'echo': False
            })
        
        return base_options


def init_database(app: Flask) -> None:
    """Initialize database with production settings"""
    
    # Configure database URL and options
    environment = app.config.get('FLASK_ENV', 'production')
    
    app.config['SQLALCHEMY_DATABASE_URI'] = DatabaseConfig.get_database_url(environment)
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = DatabaseConfig.get_engine_options(environment)
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_RECORD_QUERIES'] = environment == 'development'
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db, directory='migrations')
    
    # Set up database events for production optimization
    setup_database_events(app)
    
    logger.info(f"Database initialized for {environment} environment")


def setup_database_events(app: Flask) -> None:
    """Set up database events for production optimization"""
    
    @event.listens_for(Engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        """Set SQLite pragmas for better performance and integrity"""
        if 'sqlite' in str(dbapi_connection):
            cursor = dbapi_connection.cursor()
            # Enable foreign key constraints
            cursor.execute("PRAGMA foreign_keys=ON")
            # Set WAL mode for better concurrency
            cursor.execute("PRAGMA journal_mode=WAL")
            # Set synchronous mode for better performance
            cursor.execute("PRAGMA synchronous=NORMAL")
            # Set cache size (in KB)
            cursor.execute("PRAGMA cache_size=10000")
            # Set temp store in memory
            cursor.execute("PRAGMA temp_store=MEMORY")
            cursor.close()
    
    @event.listens_for(Engine, "connect")
    def set_postgresql_settings(dbapi_connection, connection_record):
        """Set PostgreSQL settings for production"""
        if hasattr(dbapi_connection, 'set_session'):
            # Set isolation level
            dbapi_connection.set_session(autocommit=False)


def create_tables() -> None:
    """Create all database tables"""
    from backend.models import User, Client, Program, ClientProgram, Visit, Appointment
    db.create_all()
    logger.info("Database tables created successfully")


def drop_tables() -> None:
    """Drop all database tables (use with caution!)"""
    db.drop_all()
    logger.warning("All database tables dropped")


def backup_database(backup_path: str) -> bool:
    """Create a database backup"""
    try:
        if 'sqlite' in db.engine.url.drivername:
            import shutil
            db_path = db.engine.url.database
            shutil.copy2(db_path, backup_path)
        else:
            # For PostgreSQL, use pg_dump
            import subprocess
            db_url = str(db.engine.url)
            result = subprocess.run([
                'pg_dump', db_url, '-f', backup_path
            ], capture_output=True, text=True)
            if result.returncode != 0:
                logger.error(f"Backup failed: {result.stderr}")
                return False
        
        logger.info(f"Database backed up to {backup_path}")
        return True
    except Exception as e:
        logger.error(f"Backup failed: {e}")
        return False


def check_database_health() -> Dict[str, Any]:
    """Check database connection and health"""
    try:
        # Test basic connection
        result = db.session.execute(text('SELECT 1'))
        result.close()
        
        # Get connection info
        engine_info = {
            'driver': db.engine.name,
            'url': str(db.engine.url).split('@')[-1] if '@' in str(db.engine.url) else str(db.engine.url),
            'pool_size': db.engine.pool.size() if hasattr(db.engine.pool, 'size') else 'N/A',
            'checked_out': db.engine.pool.checkedout() if hasattr(db.engine.pool, 'checkedout') else 'N/A',
        }
        
        return {
            'status': 'healthy',
            'connection': True,
            'engine_info': engine_info
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            'status': 'unhealthy',
            'connection': False,
            'error': str(e)
        }


class DatabaseManager:
    """Production database management utilities"""
    
    @staticmethod
    def get_table_stats() -> Dict[str, int]:
        """Get row counts for all tables"""
        from backend.models import User, Client, Program, ClientProgram, Visit, Appointment
        
        tables = {
            'users': User,
            'clients': Client,
            'programs': Program,
            'client_programs': ClientProgram,
            'visits': Visit,
            'appointments': Appointment
        }
        
        stats = {}
        for table_name, model in tables.items():
            try:
                stats[table_name] = db.session.query(model).count()
            except Exception as e:
                stats[table_name] = f"Error: {e}"
        
        return stats
    
    @staticmethod
    def cleanup_old_data(days: int = 365) -> Dict[str, int]:
        """Clean up old data (use with caution in production)"""
        from datetime import datetime, timedelta
        from backend.models import Visit, Appointment
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        cleanup_stats = {}
        
        try:
            # Clean up old completed appointments
            old_appointments = db.session.query(Appointment).filter(
                Appointment.date < cutoff_date,
                Appointment.status.in_(['completed', 'no_show'])
            )
            count = old_appointments.count()
            old_appointments.delete(synchronize_session=False)
            cleanup_stats['appointments_cleaned'] = count
            
            # Note: Be very careful with visit cleanup in production
            # Usually you want to keep medical records
            
            db.session.commit()
            logger.info(f"Cleaned up old data: {cleanup_stats}")
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Cleanup failed: {e}")
            cleanup_stats['error'] = str(e)
        
        return cleanup_stats
    
    @staticmethod
    def optimize_database() -> Dict[str, Any]:
        """Run database optimization commands"""
        results = {}
        
        try:
            if 'sqlite' in db.engine.url.drivername:
                # SQLite optimization
                db.session.execute(text('VACUUM'))
                db.session.execute(text('ANALYZE'))
                results['sqlite_optimization'] = 'completed'
            
            elif 'postgresql' in db.engine.url.drivername:
                # PostgreSQL optimization
                db.session.execute(text('VACUUM ANALYZE'))
                results['postgresql_optimization'] = 'completed'
            
            db.session.commit()
            logger.info("Database optimization completed")
            
        except Exception as e:
            logger.error(f"Database optimization failed: {e}")
            results['error'] = str(e)
        
        return results
