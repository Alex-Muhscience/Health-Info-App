#!/usr/bin/env python3
"""
Database Management Script for Production
Handles database migrations, initialization, and maintenance tasks.
"""

import os
import sys
import click
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from backend import create_app
from backend.database import db, migrate, DatabaseManager, backup_database, check_database_health
from backend.config import validate_config
from flask_migrate import init as migrate_init, migrate as migrate_migrate, upgrade, downgrade
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@click.group()
def cli():
    """Database management commands for Health Management System"""
    pass


@cli.command()
@click.option('--environment', '-e', default='development', help='Environment to use')
def init(environment):
    """Initialize database and create migration repository"""
    app = create_app(environment)
    
    with app.app_context():
        try:
            # Initialize migration repository if it doesn't exist
            if not os.path.exists('migrations'):
                migrate_init()
                logger.info("✅ Migration repository initialized")
            else:
                logger.info("Migration repository already exists")
            
            # Create all tables
            db.create_all()
            logger.info("✅ Database tables created")
            
            # Create initial migration
            migrate_migrate(message='Initial migration')
            logger.info("✅ Initial migration created")
            
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
            sys.exit(1)


@cli.command()
@click.option('--message', '-m', required=True, help='Migration message')
@click.option('--environment', '-e', default='development', help='Environment to use')
def create_migration(message, environment):
    """Create a new database migration"""
    app = create_app(environment)
    
    with app.app_context():
        try:
            migrate_migrate(message=message)
            logger.info(f"✅ Migration created: {message}")
        except Exception as e:
            logger.error(f"❌ Migration creation failed: {e}")
            sys.exit(1)


@cli.command()
@click.option('--environment', '-e', default='development', help='Environment to use')
def upgrade_db(environment):
    """Apply database migrations (upgrade to latest)"""
    app = create_app(environment)
    
    with app.app_context():
        try:
            upgrade()
            logger.info("✅ Database upgraded to latest migration")
        except Exception as e:
            logger.error(f"❌ Database upgrade failed: {e}")
            sys.exit(1)


@cli.command()
@click.option('--revision', '-r', help='Revision to downgrade to')
@click.option('--environment', '-e', default='development', help='Environment to use')
def downgrade_db(revision, environment):
    """Downgrade database to specific revision"""
    if not revision:
        revision = click.prompt('Enter revision to downgrade to')
    
    app = create_app(environment)
    
    with app.app_context():
        try:
            downgrade(revision=revision)
            logger.info(f"✅ Database downgraded to revision: {revision}")
        except Exception as e:
            logger.error(f"❌ Database downgrade failed: {e}")
            sys.exit(1)


@cli.command()
@click.option('--environment', '-e', default='development', help='Environment to use')
def status(environment):
    """Show database status and health"""
    app = create_app(environment)
    
    with app.app_context():
        try:
            # Check database health
            health = check_database_health()
            click.echo("\n🏥 Database Health Status")
            click.echo("=" * 40)
            click.echo(f"Status: {health['status']}")
            click.echo(f"Connection: {'✅ Connected' if health['connection'] else '❌ Disconnected'}")
            
            if 'engine_info' in health:
                click.echo(f"Driver: {health['engine_info']['driver']}")
                click.echo(f"URL: {health['engine_info']['url']}")
                click.echo(f"Pool Size: {health['engine_info']['pool_size']}")
                click.echo(f"Checked Out: {health['engine_info']['checked_out']}")
            
            if 'error' in health:
                click.echo(f"Error: {health['error']}")
            
            # Show table statistics
            stats = DatabaseManager.get_table_stats()
            click.echo("\n📊 Table Statistics")
            click.echo("=" * 40)
            for table, count in stats.items():
                click.echo(f"{table}: {count}")
                
        except Exception as e:
            logger.error(f"❌ Status check failed: {e}")
            sys.exit(1)


@cli.command()
@click.option('--path', '-p', required=True, help='Backup file path')
@click.option('--environment', '-e', default='development', help='Environment to use')
def backup(path, environment):
    """Create database backup"""
    app = create_app(environment)
    
    with app.app_context():
        try:
            success = backup_database(path)
            if success:
                logger.info(f"✅ Database backed up to: {path}")
            else:
                logger.error("❌ Backup failed")
                sys.exit(1)
        except Exception as e:
            logger.error(f"❌ Backup failed: {e}")
            sys.exit(1)


@cli.command()
@click.option('--days', '-d', default=365, help='Days of data to keep')
@click.option('--environment', '-e', default='production', help='Environment to use')
@click.confirmation_option(prompt='Are you sure you want to clean up old data?')
def cleanup(days, environment):
    """Clean up old data (DANGEROUS - use with caution)"""
    if environment != 'production':
        click.echo("❌ Cleanup only allowed in production environment")
        sys.exit(1)
    
    app = create_app(environment)
    
    with app.app_context():
        try:
            results = DatabaseManager.cleanup_old_data(days)
            if 'error' in results:
                logger.error(f"❌ Cleanup failed: {results['error']}")
                sys.exit(1)
            else:
                logger.info(f"✅ Cleanup completed: {results}")
        except Exception as e:
            logger.error(f"❌ Cleanup failed: {e}")
            sys.exit(1)


@cli.command()
@click.option('--environment', '-e', default='development', help='Environment to use')
def optimize(environment):
    """Optimize database performance"""
    app = create_app(environment)
    
    with app.app_context():
        try:
            results = DatabaseManager.optimize_database()
            if 'error' in results:
                logger.error(f"❌ Optimization failed: {results['error']}")
                sys.exit(1)
            else:
                logger.info(f"✅ Database optimized: {results}")
        except Exception as e:
            logger.error(f"❌ Optimization failed: {e}")
            sys.exit(1)


@cli.command()
def validate():
    """Validate configuration for production deployment"""
    click.echo("\n🔍 Configuration Validation")
    click.echo("=" * 40)
    
    config_status = validate_config()
    
    if config_status['issues']:
        click.echo("\n❌ Critical Issues:")
        for issue in config_status['issues']:
            click.echo(f"  • {issue}")
    
    if config_status['warnings']:
        click.echo("\n⚠️  Warnings:")
        for warning in config_status['warnings']:
            click.echo(f"  • {warning}")
    
    if config_status['valid']:
        click.echo("\n✅ Configuration is valid for production")
    else:
        click.echo("\n❌ Configuration has issues that must be resolved")
        sys.exit(1)


@cli.command()
@click.option('--environment', '-e', default='development', help='Environment to use')
def seed(environment):
    """Seed database with initial data"""
    app = create_app(environment)
    
    with app.app_context():
        try:
            from backend.init_db import init_db
            init_db()
            logger.info("✅ Database seeded with initial data")
        except Exception as e:
            logger.error(f"❌ Database seeding failed: {e}")
            sys.exit(1)


@cli.command()
@click.option('--environment', '-e', default='development', help='Environment to use')
@click.confirmation_option(prompt='Are you sure you want to reset the database? This will delete all data!')
def reset(environment):
    """Reset database (DROP ALL TABLES - DANGEROUS!)"""
    if environment == 'production':
        click.echo("❌ Database reset not allowed in production")
        sys.exit(1)
    
    app = create_app(environment)
    
    with app.app_context():
        try:
            db.drop_all()
            db.create_all()
            logger.info("✅ Database reset completed")
        except Exception as e:
            logger.error(f"❌ Database reset failed: {e}")
            sys.exit(1)


if __name__ == '__main__':
    cli()
