"""
Application entry point
Run this file to start the Flask development server
"""
from app import create_app
import os

# Create Flask application
app = create_app()

if __name__ == '__main__':
    # Run the application
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'

    app.run(host='0.0.0.0', port=port, debug=debug)
