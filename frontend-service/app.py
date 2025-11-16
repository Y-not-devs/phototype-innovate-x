"""
Phototype - Server Initialization
Main entry point for the Flask application
"""
from flask import Flask
from flask_cors import CORS

from config import Config
from routes import register_routes

def create_app():
    """Application factory pattern"""
    app = Flask(__name__)
    
    # Load configuration
    app.config['MAX_CONTENT_LENGTH'] = Config.MAX_CONTENT_LENGTH
    
    # Enable CORS
    CORS(app)
    
    # Register routes
    register_routes(app)
    
    return app

app = create_app()

if __name__ == '__main__':
    print("🚀 Starting Phototype...")
    print(f"📍 Server available at: http://localhost:{Config.PORT}")
    app.run(debug=Config.DEBUG, host=Config.HOST, port=Config.PORT)
