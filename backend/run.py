"""
Simple startup script for the Problem Statement API. This script handles Python path
configuration and starts the Flask development server with the application configuration
loaded from environment variables.

Usage:
    python run.py

Configuration:
    All settings are controlled by environment variables or defaults in Config class:
    - HOST: Server host address (default: 0.0.0.0)
    - PORT: Server port (default: 5000)
    - DEBUG: Enable debug mode (default: False)
    - MONGO_URI: MongoDB connection string (required)
    - GEMINI_API_KEY: API key for Gemini AI (required)
"""
import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.app import create_app

if __name__ == "__main__":
    print("🚀 Starting Problem Statement API...")
    
    try:
        app = create_app()
        
        host = app.config.get('HOST', '0.0.0.0')
        port = app.config.get('PORT', 5050)  # Changed from 5000 to avoid AirPlay conflicts
        debug = app.config.get('DEBUG', False)
        
        print(f"📍 Server available at: http://{host}:{port}")
        print("📖 API Endpoints:")
        print("   POST /api/analyze - Analyze problem statements and find suitable professors") 
        print("   GET  /api/tags    - Get all available tags")
        print("   GET  /api/health  - Health check")
        print("\nPress Ctrl+C to stop the server\n")
        
        app.run(host=host, port=port, debug=debug, threaded=True)
        
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Failed to start server: {str(e)}")
        sys.exit(1)
