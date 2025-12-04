
#!/usr/bin/env python3
"""
Main application - Flask app initialization
"""
from flask import Flask, jsonify
from flask_cors import CORS
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import routers
from server.routes.health import health_bp
from server.routes.showtime import showtime_bp

# Create Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# Register blueprints
app.register_blueprint(health_bp)
app.register_blueprint(showtime_bp)


@app.route('/', methods=['GET'])
def index():
    """API documentation"""
    return jsonify({
        'name': 'Showtimes REST Gateway',
        'version': '1.0',
        'endpoints': {
            'GET /health': {
                'description': 'Check service health'
            },
            'GET /showtimes': {
                'description': 'Get all showtimes'
            },
            'GET /showtimes/<id>': {
                'description': 'Get a specific showtime by ID'
            },
            'POST /showtimes': {
                'description': 'Add a new showtime',
                'body': {'movie_id': 'int', 'theater_id': 'int'}
            },
            'POST /showtimes/<id>/reserve': {
                'description': 'Reserve a seat',
                'body': {'seat': 'string', 'user': 'string'}
            },
            'DELETE /showtimes/<id>/reserve': {
                'description': 'Cancel a seat reservation',
                'body': {'seat': 'string'}
            }
        }
    })


if __name__ == '__main__':
    print("Launching REST Gateway on http://localhost:5000 astronaut! 🚀")

    app.run(debug=True, port=5000, host='0.0.0.0')