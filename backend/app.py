import sys
import os
from pathlib import Path

# Add the parent directory to the Python path so we can import backend
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend import create_app

app = create_app()

if __name__ == '__main__':
    app.run(host="127.0.0.1", port=8000, debug=True)
