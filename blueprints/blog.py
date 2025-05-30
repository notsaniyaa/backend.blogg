"""
Blog Blueprint
Handles blog post creation, editing, viewing, and commenting
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, jsonify
from flask_login import login_required, current_user
from models import BlogPost, Comment, Tag, Category, db
from forms import BlogPostForm, CommentForm
from utils import FileHandler, TextProcessor, DatabaseHelper
from ai_sentiment import sentiment_analyzer
from sqlalchemy import desc

blog_bp = Blueprint('blog', __name__)

@blog_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_post():
    """Create a new blog post with AI sentiment analysis"""
    form = BlogPostForm()

    if form.validate_on_submit():
        try:
            # Create new blog post
            post = BlogPost(
                title=form.title.data,
                content=form.content.data,
                summary=form.summary.data or TextProcessor.generate_summary(form.content.data),
                published=form.published.data,
                user_id=current_user.id
            )

            # Set category if selected
            if form.category_id.data and form.category_id.data > 0:
                post.category_id = form.category_id.data

            # Handle featured image upload
            if form.featured_image.data:
                picture_file = FileHandler.save_picture(form.featured_image.data, 'posts')
                if picture_file:
                    post.featured_image = picture_file

            # AI Sentiment Analysis
            combined_text = f"{post.title} {post.content}"
            sentiment_result = sentiment_analyzer.analyze_sentiment(combined_text)

            post.sentiment_score = sentiment_result['score']
            post.sentiment_label = sentiment_result['label']
            post.sentiment_confidence = sentiment_result['confidence']

            db.session.add(post)
            db.session.flush()  # Get the post ID

            # Handle tags
            if form.tags.data:
                tag_names = TextProcessor.extract_tags(form.tags.data)
                for tag_name in tag_names:
                    tag = DatabaseHelper.get_or_create_tag(tag_name)
                    post.tags.append(tag)

            db.session.commit()

            # Show sentiment insights
            insights = sentiment_analyzer.get_sentiment_insights(sentiment_result)
            for insight in insights:
                flash(f"AI Insight: {insight}", 'info')

            flash('Your blog post has been created successfully!', 'success')
            return redirect(url_for('blog.view_post', id=post.id))

        except Exception as e:
            db.session.rollback()
            print(f"Create post error: {e}")
            flash('An error occurred while creating your post.', 'danger')

    return render_template('blog/create_post.html', form=form)

@blog_bp.route('/post/<int:id>')
def view_post(id):
    """View a single blog post"""
    post = BlogPost.query.get_or_404(id)

    # Increment view count
    post.increment_views()

    # Get comments
    comments = Comment.query.filter_by(post_id=id, approved=True)\
                           .order_by(desc(Comment.created_at)).all()

    # Comment form for authenticated users
    comment_form = CommentForm() if current_user.is_authenticated else None

    # Related posts (same category or tags)
    related_posts = []
    if post.category:
        related_posts = BlogPost.query.filter_by(category_id=post.category_id, published=True)\
                                     .filter(BlogPost.id != post.id)\
                                     .limit(3).all()

    # AI sentiment insights
    sentiment_insights = None
    if post.sentiment_score is not None:
        sentiment_data = {
            'score': post.sentiment_score,
            'label': post.sentiment_label,
            'confidence': post.sentiment_confidence
        }
        sentiment_insights = sentiment_analyzer.get_sentiment_insights(sentiment_data)

    return render_template('blog/view_post.html',
                         post=post,
                         comments=comments,
                         comment_form=comment_form,
                         related_posts=related_posts,
                         sentiment_insights=sentiment_insights)

@blog_bp.route('/post/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_post(id):
    """Edit a blog post"""
    try:
        post = BlogPost.query.get_or_404(id)

        # Check if user owns the post
        if post.author != current_user:
            abort(403)

        form = BlogPostForm()

        if form.validate_on_submit():
            try:
                # Update post fields
                post.title = form.title.data
                post.content = form.content.data
                post.summary = form.summary.data or TextProcessor.generate_summary(form.content.data)
                post.published = form.published.data

                # Update category
                if form.category_id.data and form.category_id.data > 0:
                    post.category_id = form.category_id.data
                else:
                    post.category_id = None

                # Handle featured image upload
                if form.featured_image.data:
                    # Delete old image
                    if post.featured_image:
                        FileHandler.delete_picture(post.featured_image, 'posts')

                    picture_file = FileHandler.save_picture(form.featured_image.data, 'posts')
                    if picture_file:
                        post.featured_image = picture_file

                # Re-analyze sentiment with updated content
                combined_text = f"{post.title} {post.content}"
                sentiment_result = sentiment_analyzer.analyze_sentiment(combined_text)

                post.sentiment_score = sentiment_result['score']
                post.sentiment_label = sentiment_result['label']
                post.sentiment_confidence = sentiment_result['confidence']

                # Update tags safely
                try:
                    post.tags.clear()
                    if form.tags.data:
                        tag_names = TextProcessor.extract_tags(form.tags.data)
                        for tag_name in tag_names:
                            tag = DatabaseHelper.get_or_create_tag(tag_name)
                            if tag:
                                post.tags.append(tag)
                except Exception as e:
                    print(f"Error updating tags: {e}")

                db.session.commit()

                # Show updated sentiment insights
                try:
                    insights = sentiment_analyzer.get_sentiment_insights(sentiment_result)
                    for insight in insights:
                        flash(f"Updated AI Insight: {insight}", 'info')
                except Exception as e:
                    print(f"Error getting sentiment insights: {e}")

                flash('Your blog post has been updated successfully!', 'success')
                return redirect(url_for('blog.view_post', id=post.id))

            except Exception as e:
                db.session.rollback()
                print(f"Error updating post: {e}")
                flash('An error occurred while updating your post.', 'danger')

        elif request.method == 'GET':
            # Pre-populate form safely
            try:
                form.title.data = post.title
                form.content.data = post.content
                form.summary.data = post.summary
                form.category_id.data = post.category_id or 0
                form.published.data = post.published

                # Pre-populate tags safely
                try:
                    if post.tags:
                        form.tags.data = ', '.join([tag.name for tag in post.tags])
                except Exception as e:
                    print(f"Error loading tags: {e}")
                    form.tags.data = ''
            except Exception as e:
                print(f"Error pre-populating form: {e}")
                flash('Error loading post data.', 'warning')

        return render_template('blog/edit_post.html', form=form, post=post)

    except Exception as e:
        print(f"Edit post error: {e}")
        flash('An error occurred while loading the edit page.', 'danger')
        return redirect(url_for('main.dashboard'))

@blog_bp.route('/post/<int:id>/delete', methods=['POST'])
@login_required
def delete_post(id):
    """Delete a blog post"""
    post = BlogPost.query.get_or_404(id)

    # Check if user owns the post
    if post.author != current_user:
        abort(403)

    try:
        # Delete featured image
        if post.featured_image:
            FileHandler.delete_picture(post.featured_image, 'posts')

        db.session.delete(post)
        db.session.commit()

        flash('Your blog post has been deleted successfully.', 'success')
        return redirect(url_for('main.dashboard'))

    except Exception as e:
        db.session.rollback()
        print(f"Delete post error: {e}")
        flash('An error occurred while deleting your post.', 'danger')
        return redirect(url_for('blog.view_post', id=id))

@blog_bp.route('/post/<int:id>/comment', methods=['POST'])
@login_required
def add_comment(id):
    """Add a comment to a blog post"""
    post = BlogPost.query.get_or_404(id)
    form = CommentForm()

    if form.validate_on_submit():
        try:
            comment = Comment(
                content=form.content.data,
                user_id=current_user.id,
                post_id=id
            )

            db.session.add(comment)
            db.session.commit()

            flash('Your comment has been added successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            print(f"Add comment error: {e}")
            flash('An error occurred while adding your comment.', 'danger')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'Comment error: {error}', 'danger')

    return redirect(url_for('blog.view_post', id=id))

@blog_bp.route('/posts')
def all_posts():
    """View all published blog posts with pagination"""
    page = request.args.get('page', 1, type=int)
    category_id = request.args.get('category', 0, type=int)
    sort_by = request.args.get('sort', 'newest')

    # Base query
    query = BlogPost.query.filter_by(published=True)

    # Category filter
    if category_id > 0:
        query = query.filter_by(category_id=category_id)

    # Sorting
    if sort_by == 'oldest':
        query = query.order_by(BlogPost.created_at.asc())
    elif sort_by == 'popular':
        query = query.order_by(desc(BlogPost.views))
    elif sort_by == 'positive':
        query = query.filter(BlogPost.sentiment_label == 'positive')\
                    .order_by(desc(BlogPost.sentiment_score))
    elif sort_by == 'negative':
        query = query.filter(BlogPost.sentiment_label == 'negative')\
                    .order_by(BlogPost.sentiment_score.asc())
    else:  # newest
        query = query.order_by(desc(BlogPost.created_at))

    posts = query.paginate(page=page, per_page=12, error_out=False)

    # Get categories for filter
    categories = Category.query.all()

    return render_template('blog/all_posts.html',
                         posts=posts,
                         categories=categories,
                         current_category=category_id,
                         current_sort=sort_by)

@blog_bp.route('/my_posts')
@login_required
def my_posts():
    """View current user's blog posts"""
    page = request.args.get('page', 1, type=int)

    posts = BlogPost.query.filter_by(user_id=current_user.id)\
                          .order_by(desc(BlogPost.created_at))\
                          .paginate(page=page, per_page=10, error_out=False)

    return render_template('blog/my_posts.html', posts=posts)
