"""
Chatbot Blueprint
Handles AI chatbot interactions
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
import random

chatbot_bp = Blueprint('chatbot', __name__)


@chatbot_bp.route('/chat', methods=['POST'])
@login_required
def chat():
    """Handle chatbot messages"""
    data = request.get_json()
    message = data.get('message', '').lower().strip()

    if not message:
        return jsonify({'error': 'No message provided'}), 400

    # Generate AI response based on message content
    response = generate_ai_response(message)

    return jsonify({
        'response': response,
        'user': current_user.first_name
    })


def generate_ai_response(message):
    """Generate contextual AI responses"""

    # Sentiment analysis responses
    if any(word in message for word in ['sentiment', 'emotion', 'feeling', 'mood']):
        responses = [
            "Sentiment analysis helps understand the emotional tone of your writing. Positive posts tend to get more engagement!",
            "Our AI analyzes the sentiment of each post - positive 😊, negative 😔, or neutral 😐. This helps readers find content that matches their mood.",
            "Sentiment analysis can help you understand how your writing might be perceived. Would you like tips on writing more positive content?"
        ]
        return random.choice(responses)

    # Search and discovery responses
    elif any(word in message for word in ['search', 'find', 'discover', 'look']):
        responses = [
            "You can search for posts using keywords, filter by category, or sort by popularity. Try the search page!",
            "Use the filters on the All Posts page to find exactly what you're looking for - by category, sentiment, or popularity.",
            "Looking for something specific? The search function can help you find posts by title, content, or author."
        ]
        return random.choice(responses)

    # Favorites responses
    elif any(word in message for word in ['favorite', 'like', 'save', 'bookmark']):
        responses = [
            "Click the heart icon ❤️ on any post to add it to your favorites! You can view them all from your dashboard.",
            "Your favorites are saved in your profile. It's a great way to keep track of posts you want to read again!",
            "Favoriting posts helps you build a personal collection of content you love. Check your favorites page!"
        ]
        return random.choice(responses)

    # Writing and creating responses
    elif any(word in message for word in ['write', 'create', 'post', 'blog', 'publish']):
        responses = [
            "Ready to share your thoughts? Click 'Write New Post' to create a blog post. Our AI will analyze the sentiment!",
            "Writing tips: Be authentic, use clear headings, and don't forget to add a compelling summary. Our AI will help with sentiment analysis!",
            "When you create a post, our AI automatically analyzes its sentiment and provides insights to help improve engagement."
        ]
        return random.choice(responses)

    # Profile and account responses
    elif any(word in message for word in ['profile', 'account', 'settings', 'edit']):
        responses = [
            "You can edit your profile from the dashboard or by clicking your name in the navigation. Add a bio and profile picture!",
            "Your profile shows your posts, stats, and favorites. Make it interesting with a good bio and profile picture!",
            "Keep your profile updated! A good profile picture and bio help other users connect with your content."
        ]
        return random.choice(responses)

    # AI and technology responses
    elif any(word in message for word in ['ai', 'artificial', 'intelligence', 'technology', 'how', 'work']):
        responses = [
            "Our AI uses natural language processing to analyze the sentiment of blog posts and provide insights for better engagement.",
            "The AI features include sentiment analysis, content recommendations, and this chatbot to help you navigate the platform!",
            "AI helps make the blog smarter by understanding emotions in text and helping users find content that resonates with them."
        ]
        return random.choice(responses)

    # Help and support responses
    elif any(word in message for word in ['help', 'support', 'question', 'how to', 'tutorial']):
        responses = [
            "I'm here to help! You can ask me about finding posts, understanding sentiment analysis, writing tips, or navigating the site.",
            "Need help? I can guide you through creating posts, using favorites, searching content, or understanding AI features.",
            "Feel free to ask me anything about the blog platform! I can help with features, tips, or general questions."
        ]
        return random.choice(responses)

    # Greeting responses
    elif any(word in message for word in ['hello', 'hi', 'hey', 'greetings']):
        responses = [
            f"Hello! I'm your AI assistant. I can help you navigate the blog, find posts, or answer questions about our features!",
            f"Hi there! Ready to explore the blog? I can help you find interesting posts or explain how our AI features work.",
            f"Hey! I'm here to make your blogging experience better. What would you like to know about?"
        ]
        return random.choice(responses)

    # Default responses
    else:
        responses = [
            "That's interesting! I can help you with blog navigation, sentiment analysis, finding posts, or writing tips. What would you like to explore?",
            "I'm here to help with anything blog-related! Try asking me about sentiment analysis, searching for posts, or creating content.",
            "Great question! I specialize in helping with blog features like favorites, search, sentiment analysis, and content creation. How can I assist?",
            "I'd love to help! I can guide you through using the blog platform, understanding AI features, or finding great content to read."
        ]
        return random.choice(responses)
