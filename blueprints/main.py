"""
Main Blueprint
Handles home page, dashboard, search, and general site functionality
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import BlogPost, Category, Tag, User, Favorite, Comment, db
from sqlalchemy import or_, desc, func

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Home page with featured posts"""
    try:
        # Get featured posts (most viewed or recent) - simplified query
        featured_posts = []
        try:
            featured_posts = BlogPost.query.filter_by(published=True)\
                                          .order_by(desc(BlogPost.views))\
                                          .limit(6).all()
        except Exception as e:
            print(f"Error getting featured posts: {e}")
            # Fallback to recent posts
            try:
                featured_posts = BlogPost.query.filter_by(published=True)\
                                              .order_by(desc(BlogPost.created_at))\
                                              .limit(6).all()
            except:
                featured_posts = []

        # Get recent posts
        recent_posts = []
        try:
            recent_posts = BlogPost.query.filter_by(published=True)\
                                         .order_by(desc(BlogPost.created_at))\
                                         .limit(4).all()
        except Exception as e:
            print(f"Error getting recent posts: {e}")
            recent_posts = []

        # Get categories - simplified
        categories = []
        try:
            all_categories = Category.query.all()
            for category in all_categories:
                try:
                    post_count = BlogPost.query.filter_by(category_id=category.id, published=True).count()
                    categories.append((category, post_count))
                except:
                    categories.append((category, 0))
        except Exception as e:
            print(f"Error getting categories: {e}")
            categories = []

        # Get popular tags - simplified
        popular_tags = []
        try:
            all_tags = Tag.query.all()
            tag_counts = []
            for tag in all_tags:
                try:
                    # Count posts for this tag
                    post_count = 0
                    for post in tag.posts:
                        if post.published:
                            post_count += 1
                    if post_count > 0:
                        tag_counts.append((tag, post_count))
                except:
                    pass

            # Sort by count and take top 10
            tag_counts.sort(key=lambda x: x[1], reverse=True)
            popular_tags = tag_counts[:10]
        except Exception as e:
            print(f"Error getting popular tags: {e}")
            popular_tags = []

        # Get user stats if logged in
        user_stats = None
        if current_user.is_authenticated:
            try:
                user_stats = {
                    'total_posts': 0,
                    'total_favorites': 0
                }

                # Count user's posts safely
                try:
                    user_stats['total_posts'] = BlogPost.query.filter_by(user_id=current_user.id).count()
                except:
                    user_stats['total_posts'] = 0

                # Count user's favorites safely
                try:
                    user_stats['total_favorites'] = Favorite.query.filter_by(user_id=current_user.id).count()
                except:
                    user_stats['total_favorites'] = 0

            except Exception as e:
                print(f"Error getting user stats: {e}")
                user_stats = {'total_posts': 0, 'total_favorites': 0}

        return render_template('main/index.html',
                             featured_posts=featured_posts,
                             recent_posts=recent_posts,
                             categories=categories,
                             popular_tags=popular_tags,
                             user_stats=user_stats)
    except Exception as e:
        print(f"Index error: {e}")
        # Return minimal template with empty data
        return render_template('main/index.html',
                             featured_posts=[],
                             recent_posts=[],
                             categories=[],
                             popular_tags=[],
                             user_stats=None)

@main_bp.route('/dashboard')
@login_required
def dashboard():
    """User dashboard"""
    try:
        # User's recent posts - safe query
        user_posts = []
        try:
            user_posts = BlogPost.query.filter_by(user_id=current_user.id)\
                                      .order_by(desc(BlogPost.created_at))\
                                      .limit(5).all()
        except Exception as e:
            print(f"Error getting user posts: {e}")
            user_posts = []

        # User's favorite posts - safe query
        favorite_posts = []
        try:
            favorites = Favorite.query.filter_by(user_id=current_user.id).limit(5).all()
            for fav in favorites:
                try:
                    if fav.post and fav.post.published:
                        favorite_posts.append(fav.post)
                except:
                    continue
        except Exception as e:
            print(f"Error getting favorite posts: {e}")
            favorite_posts = []

        # Recent posts from all users - safe query
        recent_posts = []
        try:
            recent_posts = BlogPost.query.filter_by(published=True)\
                                         .filter(BlogPost.user_id != current_user.id)\
                                         .order_by(desc(BlogPost.created_at))\
                                         .limit(10).all()
        except Exception as e:
            print(f"Error getting recent posts: {e}")
            recent_posts = []

        # User statistics - safe calculation
        stats = {
            'total_posts': 0,
            'published_posts': 0,
            'total_views': 0,
            'total_favorites': 0,
            'total_comments': 0
        }

        try:
            # Count posts safely
            all_user_posts = BlogPost.query.filter_by(user_id=current_user.id).all()
            stats['total_posts'] = len(all_user_posts)
            stats['published_posts'] = len([p for p in all_user_posts if p.published])
            stats['total_views'] = sum(post.views or 0 for post in all_user_posts)
        except Exception as e:
            print(f"Error calculating post stats: {e}")

        try:
            # Count favorites safely
            stats['total_favorites'] = Favorite.query.filter_by(user_id=current_user.id).count()
        except Exception as e:
            print(f"Error counting favorites: {e}")

        try:
            # Count comments safely
            stats['total_comments'] = Comment.query.filter_by(user_id=current_user.id).count()
        except Exception as e:
            print(f"Error counting comments: {e}")

        return render_template('main/dashboard.html',
                             user_posts=user_posts,
                             favorite_posts=favorite_posts,
                             recent_posts=recent_posts,
                             stats=stats)
    except Exception as e:
        print(f"Dashboard error: {e}")
        flash('An error occurred loading your dashboard.', 'danger')
        # Return minimal dashboard
        return render_template('main/dashboard.html',
                             user_posts=[],
                             favorite_posts=[],
                             recent_posts=[],
                             stats={
                                 'total_posts': 0,
                                 'published_posts': 0,
                                 'total_views': 0,
                                 'total_favorites': 0,
                                 'total_comments': 0
                             })

@main_bp.route('/search')
def search():
    """Search functionality"""
    try:
        posts = []
        query = request.args.get('query', '').strip()
        category_id = request.args.get('category', 0, type=int)

        # Get all categories for the form
        categories = []
        try:
            categories = Category.query.all()
        except:
            categories = []

        if query:
            try:
                # Build search query
                search_query = BlogPost.query.filter_by(published=True)

                # Text search in title and content
                search_query = search_query.filter(
                    or_(
                        BlogPost.title.contains(query),
                        BlogPost.content.contains(query),
                        BlogPost.summary.contains(query)
                    )
                )

                # Category filter
                if category_id > 0:
                    search_query = search_query.filter_by(category_id=category_id)

                posts = search_query.order_by(desc(BlogPost.created_at)).all()

                flash(f'Found {len(posts)} posts for "{query}"', 'info')
            except Exception as e:
                print(f"Search query error: {e}")
                flash('An error occurred during search.', 'danger')
                posts = []

        return render_template('main/search.html',
                             posts=posts,
                             query=query,
                             categories=categories)
    except Exception as e:
        print(f"Search error: {e}")
        flash('An error occurred during search.', 'danger')
        return render_template('main/search.html',
                             posts=[],
                             query='',
                             categories=[])

@main_bp.route('/favorites')
@login_required
def favorites():
    """View user's favorite posts"""
    try:
        page = request.args.get('page', 1, type=int)

        # Get user's favorites - simplified approach
        favorite_posts = []
        try:
            favorites = Favorite.query.filter_by(user_id=current_user.id)\
                                     .order_by(desc(Favorite.created_at))\
                                     .all()

            for fav in favorites:
                try:
                    if fav.post and fav.post.published:
                        favorite_posts.append(fav.post)
                except:
                    continue
        except Exception as e:
            print(f"Error getting favorites: {e}")
            favorite_posts = []

        # Simple pagination simulation
        per_page = 10
        start = (page - 1) * per_page
        end = start + per_page
        paginated_posts = favorite_posts[start:end]

        # Create a simple pagination object
        class SimplePagination:
            def __init__(self, items, page, per_page, total):
                self.items = items
                self.page = page
                self.per_page = per_page
                self.total = total
                self.pages = (total + per_page - 1) // per_page
                self.has_prev = page > 1
                self.has_next = page < self.pages
                self.prev_num = page - 1 if self.has_prev else None
                self.next_num = page + 1 if self.has_next else None

            def iter_pages(self, left_edge=2, right_edge=2, left_current=2, right_current=2):
                last = self.pages
                for num in range(1, last + 1):
                    if num <= left_edge or \
                       (self.page - left_current - 1 < num < self.page + right_current) or \
                       num > last - right_edge:
                        yield num

        pagination = SimplePagination(paginated_posts, page, per_page, len(favorite_posts))

        return render_template('main/favorites.html', posts=pagination)
    except Exception as e:
        print(f"Favorites error: {e}")
        flash('An error occurred loading your favorites.', 'danger')
        return redirect(url_for('main.dashboard'))

@main_bp.route('/toggle_favorite/<int:post_id>', methods=['POST'])
@login_required
def toggle_favorite(post_id):
    """Toggle favorite status for a post (AJAX endpoint)"""
    try:
        post = BlogPost.query.get_or_404(post_id)

        # Check if already favorited
        favorite = Favorite.query.filter_by(user_id=current_user.id, post_id=post_id).first()

        if favorite:
            # Remove from favorites
            db.session.delete(favorite)
            is_favorited = False
            message = 'Removed from favorites'
        else:
            # Add to favorites
            favorite = Favorite(user_id=current_user.id, post_id=post_id)
            db.session.add(favorite)
            is_favorited = True
            message = 'Added to favorites'

        db.session.commit()

        # Get updated favorite count
        favorite_count = Favorite.query.filter_by(post_id=post_id).count()

        return jsonify({
            'success': True,
            'is_favorited': is_favorited,
            'message': message,
            'favorite_count': favorite_count
        })

    except Exception as e:
        db.session.rollback()
        print(f"Toggle favorite error: {e}")
        return jsonify({
            'success': False,
            'message': 'An error occurred'
        }), 500

@main_bp.route('/category/<int:category_id>')
def category_posts(category_id):
    """View posts by category"""
    try:
        category = Category.query.get_or_404(category_id)
        page = request.args.get('page', 1, type=int)

        posts = BlogPost.query.filter_by(category_id=category_id, published=True)\
                              .order_by(desc(BlogPost.created_at))\
                              .paginate(page=page, per_page=12, error_out=False)

        return render_template('main/category_posts.html', posts=posts, category=category)
    except Exception as e:
        print(f"Category posts error: {e}")
        flash('Category not found.', 'danger')
        return redirect(url_for('main.index'))

@main_bp.route('/tag/<int:tag_id>')
def tag_posts(tag_id):
    """View posts by tag"""
    try:
        tag = Tag.query.get_or_404(tag_id)
        page = request.args.get('page', 1, type=int)

        # Get posts with this tag
        posts = []
        for post in tag.posts:
            if post.published:
                posts.append(post)

        # Sort by creation date
        posts.sort(key=lambda x: x.created_at, reverse=True)

        # Simple pagination
        per_page = 12
        start = (page - 1) * per_page
        end = start + per_page
        paginated_posts = posts[start:end]

        return render_template('main/tag_posts.html', posts=paginated_posts, tag=tag)
    except Exception as e:
        print(f"Tag posts error: {e}")
        flash('Tag not found.', 'danger')
        return redirect(url_for('main.index'))

@main_bp.route('/about')
def about():
    """About page"""
    return render_template('main/about.html')

@main_bp.route('/contact')
def contact():
    """Contact page"""
    return render_template('main/contact.html')

@main_bp.route('/chatbot')
@login_required
def chatbot():
    """AI Chatbot page"""
    return render_template('main/chatbot.html')
