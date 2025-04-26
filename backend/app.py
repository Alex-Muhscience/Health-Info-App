#!/usr/bin/env python
"""Main application entry point."""
from backend import create_app
from backend.realtime.socket import socketio
import logging

# Configure logging before creating app
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = create_app()

if __name__ == '__main__':
    try:
        logger.info("Starting Health App backend server")
        socketio.run(
            app,
            host='0.0.0.0',
            port=8000,
            debug=app.config.get('DEBUG', False),
            use_reloader=app.config.get('USE_RELOADER', True),
            allow_unsafe_werkzeug=app.config.get('ALLOW_UNSAFE_WERKZEUG', False)
        )
    except Exception as e:
        logger.critical(f"Failed to start server: {str(e)}")
        raise