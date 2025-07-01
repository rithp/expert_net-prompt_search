"""
Configuration Settings Module

This module provides centralized configuration management for the Flask application.
All settings can be customized via environment variables for deployment flexibility.

Environment Variables:
- MONGO_URI: MongoDB connection string (required)
- GEMINI_API_KEY: API key for Gemini AI (required)
- HOST: Server host address (default: 0.0.0.0)
- PORT: Server port (default: 5000)
- DEBUG: Enable debug mode (default: False)
- CORS_ORIGINS: Comma-separated list of allowed origins (default: *)
- ML_MODEL_NAME: SentenceTransformer model to use
- RATELIMIT_DEFAULT: Default rate limiting (requests/minute)
"""
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

class Config:
    """
    Application configuration class.
    
    Provides all configuration settings for the Flask application with
    environment variable overrides for deployment flexibility.
    
    Attributes:
        MONGO_URI: MongoDB connection string from environment
        DATABASE_NAME: Name of the MongoDB database
        COLLECTION_NAME: Name of the professors collection
        GEMINI_API_KEY: API key for Gemini AI
        HOST: Server host address
        PORT: Server port number
        DEBUG: Debug mode flag
        MAX_CONTENT_LENGTH: Maximum request payload size (16MB)
        CORS_ORIGINS: List of allowed CORS origins
        ML_MODEL_NAME: SentenceTransformer model identifier
        ML_BATCH_SIZE: Batch size for ML operations
        ML_SIMILARITY_THRESHOLD: Similarity threshold for tag matching
        RATELIMIT_DEFAULT: Default rate limiting setting
    """
    
    # Database configuration
    MONGO_URI = os.getenv("MONGO_URI")
    DATABASE_NAME = "prof_db"
    COLLECTION_NAME = "professors"
    
    # Gemini API configuration
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    
    # Server configuration
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 5050))  # Changed from 5000 to avoid AirPlay conflicts
    
    # Performance settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max request size
    JSONIFY_PRETTYPRINT_REGULAR = False
    THREADED = True
    
    # CORS settings
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
    
    # Rate limiting (requests per minute)
    RATELIMIT_DEFAULT = os.getenv("RATELIMIT_DEFAULT", "60/minute")
    
    # ML Model settings
    ML_MODEL_NAME = os.getenv("ML_MODEL_NAME", "all-MiniLM-L6-v2")
    ML_BATCH_SIZE = int(os.getenv("ML_BATCH_SIZE", "32"))
    ML_SIMILARITY_THRESHOLD = float(os.getenv("ML_SIMILARITY_THRESHOLD", "0.7"))
    
    # MongoDB connection settings (using camelCase as required by PyMongo)
    # Note: These are passed directly to MongoClient, which requires camelCase
    MONGO_MAX_POOL_SIZE = int(os.getenv("MONGO_MAX_POOL_SIZE", "50"))
    MONGO_MIN_POOL_SIZE = int(os.getenv("MONGO_MIN_POOL_SIZE", "5"))
    MONGO_SERVER_SELECTION_TIMEOUT = int(os.getenv("MONGO_SERVER_SELECTION_TIMEOUT", "5000"))
