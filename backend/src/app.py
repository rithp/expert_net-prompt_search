"""
Flask Application Factory

Flask application setup for the Problem Statement Analysis API.
"""
import os
import logging
import atexit
import signal
import sys
from flask import Flask, jsonify
from flask_cors import CORS

from .config.settings import Config
from .services.problem_service import DatabaseService, MLService, GeminiService
from .routes.api_routes import api_bp, init_routes

# Global services for cleanup
db_service = None
ml_service = None
gemini_service = None

def setup_logging(app):
    """Configure application logging"""
    if not app.debug:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        file_handler = logging.FileHandler('logs/professor_search.log')
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        
        app.logger.setLevel(logging.INFO)
        app.logger.info('Problem Statement API startup')

def create_app():
    """Create and configure Flask application"""
    global db_service, ml_service, gemini_service
    
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Setup logging
    setup_logging(app)
    
    # Enable CORS
    CORS(app, origins=app.config['CORS_ORIGINS'])
    
    # Initialize services
    try:
        # Initialize database service
        db_service = DatabaseService(
            app.config['MONGO_URI'],
            app.config['DATABASE_NAME'],
            app.config['COLLECTION_NAME'],
            maxPoolSize=app.config.get('MONGO_MAX_POOL_SIZE', 45),
            minPoolSize=app.config.get('MONGO_MIN_POOL_SIZE', 3),
            serverSelectionTimeoutMS=app.config.get('MONGO_SERVER_SELECTION_TIMEOUT', 5000)
        )
        
        # Initialize ML service
        ml_service = MLService(
            model_name=app.config.get('ML_MODEL_NAME', 'all-MiniLM-L6-v2'),
            batch_size=app.config.get('ML_BATCH_SIZE', 32),
            similarity_threshold=app.config.get('ML_SIMILARITY_THRESHOLD', 0.7)
        )
        
        # Initialize Gemini service
        gemini_service = GeminiService(
            api_key=app.config['GEMINI_API_KEY'],
            model_name='gemini-2.0-flash'
        )
        
        # Load and preprocess data
        app.logger.info("Loading professor data from database...")
        professors = db_service.get_all_professors()
        
        if not professors:
            app.logger.warning("No professors found in database!")
        else:
            app.logger.info(f"Found {len(professors)} professors in database")
            
        ml_service.initialize(professors)
        app.logger.info("ML service initialized successfully")
        
    except Exception as e:
        app.logger.error(f"Failed to initialize services: {str(e)}")
        raise
    
    # Initialize routes with services
    init_routes(ml_service, gemini_service)
    
    # Register blueprints
    app.register_blueprint(api_bp)
    
    # Global error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "error": "Not found",
            "message": "The requested resource was not found."
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f"Server Error: {error}")
        return jsonify({
            "error": "Internal server error",
            "message": "An unexpected error occurred."
        }), 500

    # Clean up resources on shutdown
    def cleanup_resources():
        app.logger.info("Cleaning up resources...")
        
    atexit.register(cleanup_resources)
    
    # Handle SIGTERM for graceful shutdown in containers
    def handle_sigterm(signum, frame):
        app.logger.info("Received SIGTERM signal. Shutting down...")
        cleanup_resources()
        sys.exit(0)
        
    signal.signal(signal.SIGTERM, handle_sigterm)
    
    return app
