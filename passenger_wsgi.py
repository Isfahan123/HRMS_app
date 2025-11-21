import sys
import os

# Ensure correct path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load the FastAPI app
from web_app import app

# Convert FastAPI ASGI app → WSGI app
from asgiref.wsgi import WsgiToAsgi
application = WsgiToAsgi(app)
