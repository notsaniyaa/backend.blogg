from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, PasswordField, BooleanField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, Optional
from models import User, Category
from flask_login import current_user


class RegistrationForm(FlaskForm):
    """User registration form with validation"""
    username = StringField('Username', validators=[
        DataRequired(message='Username is required'),
        Length(min=4, max=20, message='Username must be between 4 and 20 characters')
    ])
    email = StringField('Email', validators=[
        DataRequired(message='Email is required'),
        Email(message='Please enter a valid email address')
    ])
    first_name = StringField('First Name', validators=[
        DataRequired(message='First name is required'),
        Length(min=2, max=50, message='First name must be between 2 and 50 characters')
    ])
    last_name = StringField('Last Name', validators=[
        DataRequired(message='Last name is required'),
        Length(min=2, max=50, message='Last name must be between 2 and 50 characters')
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message='Password is required'),
        Length(min=6, message='Password must be at least 6 characters')
    ])
    password2 = PasswordField('Confirm Password', validators=[
        DataRequired(message='Please confirm your password'),
        EqualTo('password', message='Passwords must match')
    ])
    submit = SubmitField('Register')

    def validate_username(self, username):
        """Check if username already exists"""
        try:
            user = User.query.filter_by(username=username.data.strip()).first()
            if user:
                raise ValidationError('Username already exists. Please choose a different one.')
        except Exception as e:
            # If there's a database error, let the view handle it
            pass

    def validate_email(self, email):
        """Check if email already exists"""
        try:
            user = User.query.filter_by(email=email.data.strip().lower()).first()
            if user:
                raise ValidationError('Email already registered. Please choose a different one.')
        except Exception as e:
            # If there's a database error, let the view handle it
            pass


class LoginForm(FlaskForm):
    """User login form"""
    username = StringField('Username', validators=[
        DataRequired(message='Username is required')
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message='Password is required')
    ])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Login')


class EditProfileForm(FlaskForm):
    """User profile editing form"""
    first_name = StringField('First Name', validators=[
        DataRequired(message='First name is required'),
        Length(min=2, max=50, message='First name must be between 2 and 50 characters')
    ])
    last_name = StringField('Last Name', validators=[
        DataRequired(message='Last name is required'),
        Length(min=2, max=50, message='Last name must be between 2 and 50 characters')
    ])
    email = StringField('Email', validators=[
        DataRequired(message='Email is required'),
        Email(message='Please enter a valid email address')
    ])
    bio = TextAreaField('Bio', validators=[
        Length(max=500, message='Bio cannot exceed 500 characters')
    ])
    profile_image = FileField('Profile Image', validators=[
        FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')
    ])
    submit = SubmitField('Save Changes')

    def validate_email(self, email):
        """Check if email already exists (excluding current user)"""
        try:
            if current_user.is_authenticated and email.data.strip().lower() != current_user.email.lower():
                user = User.query.filter_by(email=email.data.strip().lower()).first()
                if user:
                    raise ValidationError('Email already registered. Please choose a different one.')
        except Exception as e:
            # If there's a database error, let the view handle it
            pass


class BlogPostForm(FlaskForm):
    """Blog post creation and editing form"""
    title = StringField('Title', validators=[
        DataRequired(message='Title is required'),
        Length(min=5, max=200, message='Title must be between 5 and 200 characters')
    ])
    content = TextAreaField('Content', validators=[
        DataRequired(message='Content is required'),
        Length(min=50, message='Content must be at least 50 characters')
    ])
    summary = TextAreaField('Summary (Optional)', validators=[
        Length(max=500, message='Summary cannot exceed 500 characters')
    ])
    category_id = SelectField('Category', coerce=int, validators=[Optional()])
    tags = StringField('Tags (comma-separated)', validators=[Optional()])
    featured_image = FileField('Featured Image', validators=[
        FileAllowed(['jpg', 'png', 'jpeg', 'gif'], 'Images only!')
    ])
    published = BooleanField('Publish immediately', default=True)
    submit = SubmitField('Create Post')

    def __init__(self, *args, **kwargs):
        super(BlogPostForm, self).__init__(*args, **kwargs)
        self.load_categories()

    def load_categories(self):
        """Load categories safely"""
        try:
            categories = Category.query.all()
            self.category_id.choices = [(0, 'No Category')] + [
                (cat.id, cat.name) for cat in categories
            ]
        except Exception as e:
            print(f"Error loading categories: {e}")
            self.category_id.choices = [(0, 'No Category')]


class CommentForm(FlaskForm):
    """Comment form for blog posts"""
    content = TextAreaField('Comment', validators=[
        DataRequired(message='Comment is required'),
        Length(min=10, max=1000, message='Comment must be between 10 and 1000 characters')
    ])
    submit = SubmitField('Post Comment')


class SearchForm(FlaskForm):
    """Search form for blog posts"""
    query = StringField('Search', validators=[DataRequired()])
    category = SelectField('Category', coerce=int, validators=[Optional()])
    submit = SubmitField('Search')

    def __init__(self, *args, **kwargs):
        super(SearchForm, self).__init__(*args, **kwargs)
        try:
            self.category.choices = [(0, 'All Categories')] + [
                (cat.id, cat.name) for cat in Category.query.all()
            ]
        except:
            self.category.choices = [(0, 'All Categories')]
