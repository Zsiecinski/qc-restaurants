import os
import sys
import logging

# Set up logging
logging.basicConfig(
    filename='app.log',
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s: %(message)s'
)

# Get the current directory
current_dir = os.path.dirname(os.path.abspath(__file__))

# Add the virtual environment's site-packages to the path
VENV_PATH = os.path.join(current_dir, 'venv', 'lib', 'python3.9', 'site-packages')
if VENV_PATH not in sys.path:
    sys.path.insert(0, VENV_PATH)

# Add the application directory to the Python path
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    from app import app as application
    logging.info("Application loaded successfully")
except Exception as e:
    logging.error(f"Failed to load application: {str(e)}")
    raise 