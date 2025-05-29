from flask import Flask, render_template
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
import os
from datetime import timedelta

# Import db from models to avoid circular imports
from models import db

# Initialize other extensions
login_manager = LoginManager()
csrf = CSRFProtect()


def create_app():
    app = Flask(__name__)

    # Configuration
    app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = 'static/uploads'
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1)

    # Create upload directories
    upload_dirs = ['static/uploads', 'static/uploads/posts', 'static/uploads/profiles']
    for directory in upload_dirs:
        try:
            os.makedirs(directory, exist_ok=True)
        except Exception as e:
            print(f"Error creating directory {directory}: {e}")

    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Login manager configuration
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'

    @login_manager.user_loader
    def load_user(user_id):
        from models import User
        try:
            return User.query.get(int(user_id))
        except Exception as e:
            print(f"Error loading user: {e}")
            return None

    # Register blueprints
    from blueprints.auth import auth_bp
    from blueprints.main import main_bp
    from blueprints.blog import blog_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp)
    app.register_blueprint(blog_bp, url_prefix='/blog')

    # Error handlers
    @app.errorhandler(500)
    def internal_error(error):
        print(f"500 Error: {error}")
        db.session.rollback()
        return render_template('errors/500.html'), 500

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(Exception)
    def handle_exception(e):
        print(f"Unhandled exception: {e}")
        db.session.rollback()
        return render_template('errors/500.html'), 500

    # Create database tables
    with app.app_context():
        try:
            db.create_all()
            print("Database tables created successfully!")

            # Initialize sample data if needed
            from models import User, Category
            if not User.query.first():
                init_sample_data()
        except Exception as e:
            print(f"Database initialization error: {e}")

    return app


def init_sample_data():
    """Initialize the database with sample data"""
    from models import db, User, Category, BlogPost
    from ai_sentiment import sentiment_analyzer

    try:
        print("Initializing sample data...")

        # Create sample categories
        categories_data = [
            ('Technology', 'Posts about technology and programming', '#007bff'),
            ('Lifestyle', 'Posts about lifestyle and personal experiences', '#28a745'),
            ('Travel', 'Travel experiences and tips', '#ffc107'),
            ('Food', 'Recipes and food reviews', '#dc3545'),
            ('Health', 'Health and wellness tips', '#6f42c1')
        ]

        for name, desc, color in categories_data:
            if not Category.query.filter_by(name=name).first():
                category = Category(name=name, description=desc, color=color)
                db.session.add(category)

        # Create sample user
        if not User.query.filter_by(username='admin').first():
            admin_user = User(
                username='admin',
                email='admin@example.com',
                first_name='Admin',
                last_name='User',
                bio='Welcome to our AI-powered blog! I\'m here to help you get started.'
            )
            admin_user.set_password('admin123')
            db.session.add(admin_user)

        db.session.commit()
        print("Sample data initialized successfully!")

    except Exception as e:
        db.session.rollback()
        print(f"Error initializing sample data: {e}")


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
