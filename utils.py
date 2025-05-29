"""
Utility functions for file handling and other common operations
"""
import os
import secrets
import uuid

class FileHandler:
    """Handle file uploads and processing"""

    @staticmethod
    def save_picture(form_picture, folder, size=(800, 600)):
        """
        Save uploaded picture with random filename
        Args:
            form_picture: FileStorage object from form
            folder: subfolder in uploads directory
            size: tuple for image resizing
        Returns:
            filename: saved filename
        """
        try:
            from PIL import Image
            from flask import current_app

            # Generate random filename
            random_hex = secrets.token_hex(8)
            _, f_ext = os.path.splitext(form_picture.filename)
            picture_fn = random_hex + f_ext

            # Create full path
            upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], folder)
            os.makedirs(upload_path, exist_ok=True)
            picture_path = os.path.join(upload_path, picture_fn)

            # Resize and save image
            img = Image.open(form_picture)
            img.thumbnail(size, Image.Resampling.LANCZOS)
            img.save(picture_path, optimize=True, quality=85)
            return picture_fn

        except ImportError:
            # If PIL is not available, save without resizing
            try:
                from flask import current_app

                random_hex = secrets.token_hex(8)
                _, f_ext = os.path.splitext(form_picture.filename)
                picture_fn = random_hex + f_ext

                upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], folder)
                os.makedirs(upload_path, exist_ok=True)
                picture_path = os.path.join(upload_path, picture_fn)

                form_picture.save(picture_path)
                return picture_fn
            except Exception as e:
                print(f"Error saving image: {e}")
                return None
        except Exception as e:
            print(f"Error saving image: {e}")
            return None

    @staticmethod
    def delete_picture(filename, folder):
        """Delete picture file"""
        if filename and filename != 'default.jpg':
            try:
                from flask import current_app
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], folder, filename)
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                print(f"Error deleting file: {e}")

class TextProcessor:
    """Process and format text content"""

    @staticmethod
    def extract_tags(tag_string):
        """Extract and clean tags from comma-separated string"""
        if not tag_string:
            return []

        try:
            tags = [tag.strip().lower() for tag in tag_string.split(',')]
            # Remove empty tags and duplicates
            tags = list(set([tag for tag in tags if tag]))
            return tags[:10]  # Limit to 10 tags
        except Exception as e:
            return []

    @staticmethod
    def generate_summary(content, max_length=200):
        """Generate summary from content if not provided"""
        try:
            if not content or len(content) <= max_length:
                return content

            # Find the last complete sentence within the limit
            truncated = content[:max_length]
            last_period = truncated.rfind('.')

            if last_period > max_length * 0.7:  # If we found a period in the last 30%
                return truncated[:last_period + 1]
            else:
                return truncated + "..."
        except Exception as e:
            return content[:max_length] + "..." if content else ""

class DatabaseHelper:
    """Helper functions for database operations"""

    @staticmethod
    def get_or_create_tag(tag_name):
        """Get existing tag or create new one"""
        try:
            from models import Tag, db

            tag = Tag.query.filter_by(name=tag_name).first()
            if not tag:
                tag = Tag(name=tag_name)
                db.session.add(tag)
            return tag
        except Exception as e:
            print(f"Error with tag: {e}")
            return None

    @staticmethod
    def get_or_create_category(category_name):
        """Get existing category or create new one"""
        try:
            from models import Category, db

            category = Category.query.filter_by(name=category_name).first()
            if not category:
                category = Category(name=category_name)
                db.session.add(category)
            return category
        except Exception as e:
            print(f"Error with category: {e}")
            return None
