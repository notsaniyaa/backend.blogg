"""
Authentication Blueprint
Handles user registration, login, logout, and profile management
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from models import User, BlogPost, Favorite, db, Comment
from forms import RegistrationForm, LoginForm, EditProfileForm
from utils import FileHandler
from sqlalchemy import desc

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = RegistrationForm()

    if form.validate_on_submit():
        try:
            # Check if username already exists
            existing_user = User.query.filter_by(username=form.username.data.strip()).first()
            if existing_user:
                flash('Username already exists. Please choose a different one.', 'danger')
                return render_template('auth/register.html', form=form)

            # Check if email already exists
            existing_email = User.query.filter_by(email=form.email.data.strip().lower()).first()
            if existing_email:
                flash('Email already registered. Please choose a different one.', 'danger')
                return render_template('auth/register.html', form=form)

            # Create new user
            user = User(
                username=form.username.data.strip(),
                email=form.email.data.strip().lower(),
                first_name=form.first_name.data.strip(),
                last_name=form.last_name.data.strip()
            )
            user.set_password(form.password.data)

            # Add to database
            db.session.add(user)
            db.session.commit()

            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('auth.login'))

        except Exception as e:
            db.session.rollback()
            print(f"Registration error: {e}")
            flash('An error occurred during registration. Please try again.', 'danger')

    return render_template('auth/register.html', form=form)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = LoginForm()

    if form.validate_on_submit():
        try:
            user = User.query.filter_by(username=form.username.data.strip()).first()

            if user and user.check_password(form.password.data):
                login_user(user, remember=form.remember_me.data)
                next_page = request.args.get('next')

                if not next_page or not next_page.startswith('/'):
                    next_page = url_for('main.dashboard')

                flash(f'Welcome back, {user.first_name}!', 'success')
                return redirect(next_page)
            else:
                flash('Invalid username or password.', 'danger')
        except Exception as e:
            print(f"Login error: {e}")
            flash('An error occurred during login. Please try again.', 'danger')

    return render_template('auth/login.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    """User logout"""
    try:
        logout_user()
        flash('You have been logged out successfully.', 'info')
    except Exception as e:
        print(f"Logout error: {e}")
        flash('Logged out.', 'info')

    return redirect(url_for('main.index'))

@auth_bp.route('/profile')
@auth_bp.route('/profile/<int:user_id>')
def profile(user_id=None):
    """View user profile"""
    try:
        if user_id is None:
            if current_user.is_authenticated:
                user_id = current_user.id
            else:
                flash('Please log in to view your profile.', 'warning')
                return redirect(url_for('auth.login'))

        user = User.query.get_or_404(user_id)

        # Get user's recent posts
        recent_posts = []
        try:
            recent_posts = BlogPost.query.filter_by(user_id=user_id, published=True)\
                                         .order_by(desc(BlogPost.created_at))\
                                         .limit(5).all()
        except Exception as e:
            print(f"Error getting recent posts: {e}")

        # Get user's favorite posts (only if viewing own profile)
        favorite_posts = []
        if current_user.is_authenticated and current_user.id == user_id:
            try:
                favorites = Favorite.query.filter_by(user_id=user_id).limit(5).all()
                favorite_posts = [fav.post for fav in favorites if fav.post]
            except Exception as e:
                print(f"Error getting favorite posts: {e}")

        # User statistics
        stats = {
            'total_posts': 0,
            'total_favorites': 0,
            'total_comments': 0
        }

        try:
            # Count published posts
            stats['total_posts'] = BlogPost.query.filter_by(user_id=user_id, published=True).count()
        except:
            pass

        try:
            # Count favorites
            stats['total_favorites'] = Favorite.query.filter_by(user_id=user_id).count()
        except:
            pass

        try:
            # Count comments
            stats['total_comments'] = Comment.query.filter_by(user_id=user_id).count()
        except:
            pass

        return render_template('auth/profile.html',
                             user=user,
                             recent_posts=recent_posts,
                             favorite_posts=favorite_posts,
                             stats=stats)
    except Exception as e:
        print(f"Profile error: {e}")
        flash('Profile not found.', 'danger')
        return redirect(url_for('main.index'))

@auth_bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Edit user profile"""
    try:
        form = EditProfileForm()

        if form.validate_on_submit():
            try:
                # Update basic info
                current_user.first_name = form.first_name.data.strip()
                current_user.last_name = form.last_name.data.strip()
                current_user.email = form.email.data.strip().lower()
                current_user.bio = form.bio.data.strip() if form.bio.data else None

                # Handle profile image upload
                if form.profile_image.data:
                    try:
                        # Delete old image
                        if current_user.profile_image and current_user.profile_image != 'default.jpg':
                            FileHandler.delete_picture(current_user.profile_image, 'profiles')

                        picture_file = FileHandler.save_picture(form.profile_image.data, 'profiles')
                        if picture_file:
                            current_user.profile_image = picture_file
                    except Exception as e:
                        print(f"Image upload error: {e}")
                        flash('Error uploading image. Profile updated without image.', 'warning')

                db.session.commit()
                flash('Your profile has been updated successfully!', 'success')
                return redirect(url_for('auth.profile', user_id=current_user.id))

            except Exception as e:
                db.session.rollback()
                print(f"Profile update error: {e}")
                flash('An error occurred while updating your profile.', 'danger')

        elif request.method == 'GET':
            # Pre-populate form with current user data
            form.first_name.data = current_user.first_name
            form.last_name.data = current_user.last_name
            form.email.data = current_user.email
            form.bio.data = current_user.bio

        return render_template('auth/edit_profile.html', form=form)

    except Exception as e:
        print(f"Edit profile error: {e}")
        flash('An error occurred loading the edit profile page.', 'danger')
        return redirect(url_for('auth.profile'))
