import sys
import os

# Add the backend directory to python path so Flask imports resolve correctly
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend'))
sys.path.append(backend_dir)

from app import create_app

app = create_app()
