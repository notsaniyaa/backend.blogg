"""
AI Sentiment Analysis Module
Uses a lightweight approach for sentiment analysis without external APIs
"""
import re

class SentimentAnalyzer:
    """AI-powered sentiment analysis for blog posts"""

    def __init__(self):
        """Initialize the sentiment analyzer"""
        self.use_vader = False
        self.analyzer = None

        try:
            # Try to use NLTK's VADER sentiment analyzer (more accurate)
            import nltk
            from nltk.sentiment import SentimentIntensityAnalyzer
            try:
                nltk.download('vader_lexicon', quiet=True)
                self.analyzer = SentimentIntensityAnalyzer()
                self.use_vader = True
            except:
                pass
        except ImportError:
            pass

    def clean_text(self, text):
        """Clean and preprocess text for analysis"""
        if not text:
            return ""

        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        # Remove extra whitespace
        text = ' '.join(text.split())
        # Remove special characters but keep punctuation for sentiment
        text = re.sub(r'[^\w\s.,!?;:]', '', text)
        return text.strip()

    def analyze_sentiment(self, text):
        """
        Analyze sentiment of given text
        Returns: dict with score, label, and confidence
        """
        if not text or len(text.strip()) < 10:
            return {
                'score': 0.0,
                'label': 'neutral',
                'confidence': 0.0
            }

        # Clean the text
        clean_text = self.clean_text(text)

        if self.use_vader and self.analyzer:
            return self._analyze_with_vader(clean_text)
        else:
            return self._analyze_with_simple(clean_text)

    def _analyze_with_vader(self, text):
        """Analyze sentiment using NLTK's VADER"""
        try:
            scores = self.analyzer.polarity_scores(text)

            # VADER returns compound score between -1 and 1
            compound_score = scores['compound']

            # Determine label based on compound score
            if compound_score >= 0.05:
                label = 'positive'
            elif compound_score <= -0.05:
                label = 'negative'
            else:
                label = 'neutral'

            # Calculate confidence based on the absolute value
            confidence = abs(compound_score)

            return {
                'score': compound_score,
                'label': label,
                'confidence': confidence
            }
        except Exception as e:
            return self._analyze_with_simple(text)

    def _analyze_with_simple(self, text):
        """Simple sentiment analysis using word lists"""
        try:
            # Simple positive and negative word lists
            positive_words = [
                'good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic',
                'awesome', 'brilliant', 'outstanding', 'superb', 'magnificent',
                'love', 'like', 'enjoy', 'happy', 'pleased', 'satisfied',
                'beautiful', 'perfect', 'best', 'incredible', 'remarkable'
            ]

            negative_words = [
                'bad', 'terrible', 'awful', 'horrible', 'disgusting', 'hate',
                'dislike', 'angry', 'sad', 'disappointed', 'frustrated',
                'worst', 'pathetic', 'useless', 'boring', 'annoying',
                'difficult', 'problem', 'issue', 'wrong', 'error', 'fail'
            ]

            words = text.lower().split()
            positive_count = sum(1 for word in words if word in positive_words)
            negative_count = sum(1 for word in words if word in negative_words)

            total_sentiment_words = positive_count + negative_count

            if total_sentiment_words == 0:
                return {
                    'score': 0.0,
                    'label': 'neutral',
                    'confidence': 0.0
                }

            # Calculate score
            score = (positive_count - negative_count) / len(words)

            # Determine label
            if score > 0.01:
                label = 'positive'
            elif score < -0.01:
                label = 'negative'
            else:
                label = 'neutral'

            # Calculate confidence
            confidence = min(total_sentiment_words / len(words) * 2, 1.0)

            return {
                'score': score,
                'label': label,
                'confidence': confidence
            }
        except Exception as e:
            return {
                'score': 0.0,
                'label': 'neutral',
                'confidence': 0.0
            }

    def get_sentiment_insights(self, sentiment_data):
        """
        Generate human-readable insights from sentiment analysis
        """
        try:
            score = sentiment_data.get('score', 0)
            label = sentiment_data.get('label', 'neutral')
            confidence = sentiment_data.get('confidence', 0)

            insights = []

            # Confidence level
            if confidence > 0.7:
                confidence_level = "high"
            elif confidence > 0.4:
                confidence_level = "moderate"
            else:
                confidence_level = "low"

            insights.append(f"Sentiment: {label.title()} (confidence: {confidence_level})")

            # Specific insights based on sentiment
            if label == 'positive':
                if score > 0.5:
                    insights.append("This post has a very positive tone that may engage readers well.")
                else:
                    insights.append("This post has a positive tone that should resonate with readers.")
            elif label == 'negative':
                if score < -0.5:
                    insights.append("This post has a strong negative tone. Consider if this aligns with your intended message.")
                else:
                    insights.append("This post has a negative tone. This might be appropriate for critical or serious topics.")
            else:
                insights.append("This post has a neutral tone, which is good for informational content.")

            return insights
        except Exception as e:
            return ["Sentiment analysis completed."]

# Global instance
sentiment_analyzer = SentimentAnalyzer()
