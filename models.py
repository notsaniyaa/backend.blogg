from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# Initialize db here to avoid circular imports
db = SQLAlchemy()


class User(UserMixin, db.Model):
    """User model for authentication and user management"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    bio = db.Column(db.Text)
    profile_image = db.Column(db.String(200), default='default.jpg')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    # Relationships with proper lazy loading
    posts = db.relationship('BlogPost', backref='author', lazy='dynamic', cascade='all, delete-orphan')
    comments = db.relationship('Comment', backref='author', lazy='dynamic', cascade='all, delete-orphan')
    favorites = db.relationship('Favorite', backref='user', lazy='dynamic', cascade='all, delete-orphan')

    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check if provided password matches hash"""
        return check_password_hash(self.password_hash, password)

    def get_full_name(self):
        """Return user's full name"""
        return f"{self.first_name} {self.last_name}"

    def get_favorite_posts(self):
        """Get user's favorite posts safely"""
        try:
            favorites = self.favorites.all()
            return [fav.post for fav in favorites if fav.post and fav.post.published]
        except Exception as e:
            print(f"Error getting favorite posts: {e}")
            return []

    def __repr__(self):
        return f'<User {self.username}>'


class BlogPost(db.Model):
    """Blog post model with AI sentiment analysis"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    summary = db.Column(db.String(500))
    featured_image = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published = db.Column(db.Boolean, default=True)
    views = db.Column(db.Integer, default=0)

    # AI Sentiment Analysis fields
    sentiment_score = db.Column(db.Float)  # -1 to 1 (negative to positive)
    sentiment_label = db.Column(db.String(20))  # 'positive', 'negative', 'neutral'
    sentiment_confidence = db.Column(db.Float)  # 0 to 1

    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))

    # Relationships with proper lazy loading
    comments = db.relationship('Comment', backref='post', lazy='dynamic', cascade='all, delete-orphan')
    favorites = db.relationship('Favorite', backref='post', lazy='dynamic', cascade='all, delete-orphan')
    tags = db.relationship('Tag', secondary='post_tags', back_populates='posts')

    def increment_views(self):
        """Increment post view count safely"""
        try:
            self.views = (self.views or 0) + 1
            db.session.commit()
        except Exception as e:
            print(f"Error incrementing views: {e}")
            db.session.rollback()

    def get_sentiment_emoji(self):
        """Return emoji based on sentiment"""
        if self.sentiment_label == 'positive':
            return '😊'
        elif self.sentiment_label == 'negative':
            return '😔'
        else:
            return '😐'

    def get_favorite_count(self):
        """Get number of favorites for this post safely"""
        try:
            return self.favorites.count()
        except Exception as e:
            print(f"Error getting favorite count: {e}")
            return 0

    def is_favorited_by(self, user):
        """Check if post is favorited by specific user safely"""
        if not user or not user.is_authenticated:
            return False
        try:
            return self.favorites.filter_by(user_id=user.id).first() is not None
        except Exception as e:
            print(f"Error checking favorite status: {e}")
            return False

    def __repr__(self):
        return f'<BlogPost {self.title}>'


class Category(db.Model):
    """Category model for organizing blog posts"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)
    color = db.Column(db.String(7), default='#007bff')  # Hex color

    # Relationships
    posts = db.relationship('BlogPost', backref='category', lazy='dynamic')

    def __repr__(self):
        return f'<Category {self.name}>'


class Tag(db.Model):
    """Tag model for blog post tagging"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), unique=True, nullable=False)

    # Relationships
    posts = db.relationship('BlogPost', secondary='post_tags', back_populates='tags')

    def __repr__(self):
        return f'<Tag {self.name}>'


# Association table for many-to-many relationship between posts and tags
post_tags = db.Table('post_tags',
                     db.Column('post_id', db.Integer, db.ForeignKey('blog_post.id'), primary_key=True),
                     db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
                     )


class Comment(db.Model):
    """Comment model for blog post comments"""
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    approved = db.Column(db.Boolean, default=True)

    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('blog_post.id'), nullable=False)

    def __repr__(self):
        return f'<Comment {self.id}>'


class Favorite(db.Model):
    """Favorite model for user's favorite posts"""
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('blog_post.id'), nullable=False)

    # Ensure unique user-post combinations
    __table_args__ = (db.UniqueConstraint('user_id', 'post_id', name='unique_user_post_favorite'),)

    def __repr__(self):
        return f'<Favorite User:{self.user_id} Post:{self.post_id}>'
