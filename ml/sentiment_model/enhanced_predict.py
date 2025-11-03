"""
Enhanced Sentiment Analysis Model

World-class sentiment detection with:
1. Aspect-based sentiment analysis
2. Emotion detection (beyond just positive/negative)
3. Intensity scoring
4. Trajectory prediction
5. Multi-dimensional analysis
"""

from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import torch
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import re
from collections import defaultdict


@dataclass
class AspectSentiment:
    """Sentiment for a specific aspect"""
    aspect: str
    sentiment: str  # positive, negative, neutral
    confidence: float
    mentions: List[str]  # Text snippets mentioning this aspect


@dataclass
class EmotionScore:
    """Multi-emotion classification"""
    primary_emotion: str
    emotions: Dict[str, float]  # emotion -> score
    valence: float  # -1 (negative) to 1 (positive)
    arousal: float  # 0 (calm) to 1 (excited)


@dataclass
class EnhancedSentimentResult:
    """Comprehensive sentiment analysis result"""
    # Basic sentiment
    overall_sentiment: str
    overall_confidence: float

    # Intensity and modifiers
    intensity: float  # 0-1 scale
    has_intensifiers: bool
    has_negation: bool

    # Aspect-based analysis
    aspects: List[AspectSentiment]

    # Emotion detection
    emotions: EmotionScore

    # Urgency and priority
    urgency_score: float  # 0-1 scale
    is_urgent: bool

    # Trajectory indicators
    trajectory_indicators: Dict[str, float]

    # Raw text features
    text_length: int
    has_exclamation: bool
    has_caps: bool
    question_count: int


class EnhancedSentimentAnalyzer:
    """
    World-class sentiment analyzer with comprehensive features
    """

    def __init__(self, device: Optional[str] = None):
        """
        Initialize enhanced sentiment analyzer

        Args:
            device: Device to use ('cuda' or 'cpu'). Auto-detect if None.
        """
        if device is None:
            self.device = 0 if torch.cuda.is_available() else -1
        else:
            self.device = 0 if device == 'cuda' and torch.cuda.is_available() else -1

        # Main sentiment model
        self.sentiment_model = pipeline(
            "sentiment-analysis",
            model="distilbert-base-uncased-finetuned-sst-2-english",
            device=self.device
        )

        # Emotion classification model (using sentiment as proxy)
        # In production, use a dedicated emotion model like:
        # "j-hartmann/emotion-english-distilroberta-base"
        self.emotion_model = self.sentiment_model  # Placeholder

        # Aspect categories with keywords
        self.aspect_keywords = {
            'product_quality': {
                'keywords': ['quality', 'build', 'material', 'durability', 'reliable', 'robust', 'sturdy'],
                'positive': ['excellent', 'high-quality', 'well-made', 'premium', 'solid'],
                'negative': ['poor', 'cheap', 'flimsy', 'breaks', 'defective']
            },
            'customer_service': {
                'keywords': ['support', 'service', 'help', 'representative', 'agent', 'staff', 'team'],
                'positive': ['helpful', 'responsive', 'friendly', 'professional', 'courteous'],
                'negative': ['rude', 'unhelpful', 'slow', 'unresponsive', 'incompetent']
            },
            'user_experience': {
                'keywords': ['interface', 'ui', 'ux', 'navigation', 'design', 'layout', 'usability'],
                'positive': ['intuitive', 'easy', 'clean', 'simple', 'user-friendly'],
                'negative': ['confusing', 'complicated', 'difficult', 'cluttered', 'unintuitive']
            },
            'performance': {
                'keywords': ['fast', 'slow', 'speed', 'performance', 'load', 'lag', 'responsive'],
                'positive': ['fast', 'quick', 'instant', 'smooth', 'efficient'],
                'negative': ['slow', 'sluggish', 'laggy', 'timeout', 'unresponsive']
            },
            'value': {
                'keywords': ['price', 'cost', 'value', 'worth', 'expensive', 'cheap', 'affordable'],
                'positive': ['affordable', 'worth', 'value', 'reasonable', 'bargain'],
                'negative': ['expensive', 'overpriced', 'costly', 'waste', 'not worth']
            },
            'features': {
                'keywords': ['feature', 'functionality', 'capability', 'function', 'option'],
                'positive': ['useful', 'powerful', 'comprehensive', 'versatile', 'robust'],
                'negative': ['missing', 'lacking', 'limited', 'insufficient', 'basic']
            }
        }

        # Emotion mapping (simplified - in production use dedicated model)
        self.emotion_keywords = {
            'frustrated': ['frustrated', 'annoying', 'irritating', 'aggravating'],
            'angry': ['angry', 'furious', 'outraged', 'infuriated', 'livid'],
            'disappointed': ['disappointed', 'let down', 'underwhelmed', 'dissatisfied'],
            'satisfied': ['satisfied', 'content', 'pleased', 'happy'],
            'delighted': ['delighted', 'thrilled', 'excited', 'ecstatic', 'overjoyed'],
            'grateful': ['grateful', 'thankful', 'appreciative', 'thank you'],
            'confused': ['confused', 'unclear', 'uncertain', 'puzzled'],
            'worried': ['worried', 'concerned', 'anxious', 'nervous']
        }

        # Urgency indicators
        self.urgency_keywords = {
            'high': ['urgent', 'immediately', 'asap', 'emergency', 'critical', 'now', 'right away'],
            'temporal': ['today', 'tonight', 'deadline', 'soon'],
            'impact': ['blocking', 'preventing', 'unable', 'cannot', 'broken', 'down', 'outage']
        }

        # Intensifiers and diminishers
        self.intensifiers = ['very', 'extremely', 'absolutely', 'completely', 'totally',
                            'really', 'incredibly', 'exceptionally', 'remarkably', 'highly']
        self.diminishers = ['somewhat', 'slightly', 'a bit', 'kind of', 'sort of',
                           'fairly', 'rather', 'quite', 'moderately', 'a little']

        # Negation words
        self.negations = ["not", "no", "never", "neither", "nobody", "nothing",
                         "nowhere", "none", "n't", "hardly", "barely", "scarcely"]

    def analyze(self, text: str) -> EnhancedSentimentResult:
        """
        Perform comprehensive sentiment analysis

        Args:
            text: Input text to analyze

        Returns:
            EnhancedSentimentResult with all analysis components
        """
        if not text or not text.strip():
            return self._empty_result()

        text = text.strip()
        text_lower = text.lower()

        # 1. Basic sentiment
        basic_sentiment = self.sentiment_model(text)[0]
        overall_sentiment = basic_sentiment['label'].lower()
        overall_confidence = basic_sentiment['score']

        # 2. Intensity scoring
        intensity = self._calculate_intensity(text, text_lower)
        has_intensifiers = any(word in text_lower.split() for word in self.intensifiers)
        has_negation = any(neg in text_lower for neg in self.negations)

        # 3. Aspect-based sentiment
        aspects = self._analyze_aspects(text, text_lower)

        # 4. Emotion detection
        emotions = self._detect_emotions(text, text_lower, overall_sentiment)

        # 5. Urgency scoring
        urgency_score = self._calculate_urgency(text, text_lower)
        is_urgent = urgency_score > 0.6

        # 6. Trajectory indicators
        trajectory_indicators = self._extract_trajectory_indicators(text, text_lower)

        # 7. Text features
        text_length = len(text)
        has_exclamation = '!' in text
        has_caps = any(word.isupper() and len(word) > 2 for word in text.split())
        question_count = text.count('?')

        return EnhancedSentimentResult(
            overall_sentiment=overall_sentiment,
            overall_confidence=overall_confidence,
            intensity=intensity,
            has_intensifiers=has_intensifiers,
            has_negation=has_negation,
            aspects=aspects,
            emotions=emotions,
            urgency_score=urgency_score,
            is_urgent=is_urgent,
            trajectory_indicators=trajectory_indicators,
            text_length=text_length,
            has_exclamation=has_exclamation,
            has_caps=has_caps,
            question_count=question_count
        )

    def _calculate_intensity(self, text: str, text_lower: str) -> float:
        """Calculate sentiment intensity"""
        words = text_lower.split()
        intensity = 0.5  # Base

        # Intensifiers increase intensity
        intensifier_count = sum(1 for word in words if word in self.intensifiers)
        intensity += intensifier_count * 0.15

        # Diminishers decrease intensity
        diminisher_count = sum(1 for word in words if word in self.diminishers)
        intensity -= diminisher_count * 0.1

        # Exclamation marks
        exclamations = text.count('!')
        intensity += min(exclamations * 0.05, 0.2)

        # ALL CAPS words
        caps_words = sum(1 for word in text.split() if word.isupper() and len(word) > 2)
        intensity += min(caps_words * 0.05, 0.15)

        # Repeated punctuation (!!!, ???)
        if '!!!' in text or '???' in text:
            intensity += 0.1

        return float(np.clip(intensity, 0.0, 1.0))

    def _analyze_aspects(self, text: str, text_lower: str) -> List[AspectSentiment]:
        """Analyze sentiment for specific aspects"""
        aspects = []

        for aspect_name, aspect_config in self.aspect_keywords.items():
            # Check if aspect is mentioned
            keywords = aspect_config['keywords']
            mentions = [kw for kw in keywords if kw in text_lower]

            if not mentions:
                continue

            # Determine aspect sentiment based on context
            # Simple approach: check for positive/negative keywords nearby
            positive_words = aspect_config.get('positive', [])
            negative_words = aspect_config.get('negative', [])

            pos_count = sum(1 for word in positive_words if word in text_lower)
            neg_count = sum(1 for word in negative_words if word in text_lower)

            if pos_count > neg_count:
                sentiment = 'positive'
                confidence = min(0.6 + pos_count * 0.1, 0.95)
            elif neg_count > pos_count:
                sentiment = 'negative'
                confidence = min(0.6 + neg_count * 0.1, 0.95)
            else:
                sentiment = 'neutral'
                confidence = 0.5

            aspects.append(AspectSentiment(
                aspect=aspect_name,
                sentiment=sentiment,
                confidence=confidence,
                mentions=mentions
            ))

        return aspects

    def _detect_emotions(self, text: str, text_lower: str, base_sentiment: str) -> EmotionScore:
        """Detect specific emotions beyond positive/negative"""
        emotion_scores = defaultdict(float)

        # Check for emotion keywords
        for emotion, keywords in self.emotion_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    emotion_scores[emotion] += 1.0

        # Normalize scores
        if emotion_scores:
            total = sum(emotion_scores.values())
            emotion_scores = {k: v/total for k, v in emotion_scores.items()}
            primary_emotion = max(emotion_scores, key=emotion_scores.get)
        else:
            # Default based on sentiment
            if base_sentiment == 'positive':
                primary_emotion = 'satisfied'
                emotion_scores = {'satisfied': 1.0}
            else:
                primary_emotion = 'disappointed'
                emotion_scores = {'disappointed': 1.0}

        # Calculate valence and arousal
        negative_emotions = {'frustrated', 'angry', 'disappointed', 'worried'}
        positive_emotions = {'satisfied', 'delighted', 'grateful'}
        high_arousal_emotions = {'angry', 'delighted', 'frustrated'}

        # Valence: -1 (very negative) to 1 (very positive)
        valence = 0.0
        for emotion, score in emotion_scores.items():
            if emotion in positive_emotions:
                valence += score
            elif emotion in negative_emotions:
                valence -= score

        # Arousal: 0 (calm) to 1 (excited/agitated)
        arousal = 0.5
        for emotion, score in emotion_scores.items():
            if emotion in high_arousal_emotions:
                arousal += score * 0.3
        arousal = min(arousal, 1.0)

        return EmotionScore(
            primary_emotion=primary_emotion,
            emotions=dict(emotion_scores),
            valence=float(np.clip(valence, -1.0, 1.0)),
            arousal=float(arousal)
        )

    def _calculate_urgency(self, text: str, text_lower: str) -> float:
        """Calculate urgency score"""
        urgency = 0.0

        # Check urgency keywords
        for category, keywords in self.urgency_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    if category == 'high':
                        urgency += 0.3
                    elif category == 'temporal':
                        urgency += 0.2
                    else:  # impact
                        urgency += 0.25

        # Multiple exclamation marks indicate urgency
        if '!!' in text:
            urgency += 0.15

        # ALL CAPS words indicate urgency
        caps_words = sum(1 for word in text.split() if word.isupper() and len(word) > 2)
        if caps_words > 0:
            urgency += min(caps_words * 0.1, 0.2)

        return float(np.clip(urgency, 0.0, 1.0))

    def _extract_trajectory_indicators(self, text: str, text_lower: str) -> Dict[str, float]:
        """Extract indicators of sentiment trajectory"""
        indicators = {
            'improvement_signal': 0.0,
            'deterioration_signal': 0.0,
            'satisfaction_change': 0.0
        }

        # Improvement signals
        improvement_keywords = ['better', 'improved', 'fixed', 'resolved', 'solved',
                               'working now', 'thank you', 'appreciate']
        improvement_count = sum(1 for kw in improvement_keywords if kw in text_lower)
        indicators['improvement_signal'] = min(improvement_count * 0.3, 1.0)

        # Deterioration signals
        deterioration_keywords = ['worse', 'still broken', 'still not', 'again',
                                 'another issue', 'now broken', 'stopped working']
        deterioration_count = sum(1 for kw in deterioration_keywords if kw in text_lower)
        indicators['deterioration_signal'] = min(deterioration_count * 0.3, 1.0)

        # Overall satisfaction change
        indicators['satisfaction_change'] = indicators['improvement_signal'] - indicators['deterioration_signal']

        return indicators

    def _empty_result(self) -> EnhancedSentimentResult:
        """Return empty result for invalid input"""
        return EnhancedSentimentResult(
            overall_sentiment='neutral',
            overall_confidence=0.5,
            intensity=0.5,
            has_intensifiers=False,
            has_negation=False,
            aspects=[],
            emotions=EmotionScore(
                primary_emotion='neutral',
                emotions={'neutral': 1.0},
                valence=0.0,
                arousal=0.0
            ),
            urgency_score=0.0,
            is_urgent=False,
            trajectory_indicators={
                'improvement_signal': 0.0,
                'deterioration_signal': 0.0,
                'satisfaction_change': 0.0
            },
            text_length=0,
            has_exclamation=False,
            has_caps=False,
            question_count=0
        )

    def to_dict(self, result: EnhancedSentimentResult) -> Dict:
        """Convert result to dictionary"""
        return {
            'overall_sentiment': result.overall_sentiment,
            'overall_confidence': result.overall_confidence,
            'intensity': result.intensity,
            'has_intensifiers': result.has_intensifiers,
            'has_negation': result.has_negation,
            'aspects': [asdict(aspect) for aspect in result.aspects],
            'emotions': asdict(result.emotions),
            'urgency_score': result.urgency_score,
            'is_urgent': result.is_urgent,
            'trajectory_indicators': result.trajectory_indicators,
            'text_features': {
                'length': result.text_length,
                'has_exclamation': result.has_exclamation,
                'has_caps': result.has_caps,
                'question_count': result.question_count
            }
        }


# Global instance
enhanced_analyzer = EnhancedSentimentAnalyzer()


def analyze_text(text: str) -> Dict:
    """
    Convenience function for analyzing text

    Args:
        text: Text to analyze

    Returns:
        Dictionary with analysis results
    """
    result = enhanced_analyzer.analyze(text)
    return enhanced_analyzer.to_dict(result)


if __name__ == "__main__":
    # Test the enhanced analyzer
    test_texts = [
        "This product is absolutely terrible! It broke after just one day. Very disappointed.",
        "The customer service team was extremely helpful and resolved my issue quickly. Thank you!",
        "The interface is somewhat confusing, but the performance is good.",
        "URGENT: The system is completely down and we cannot access anything. Need help ASAP!",
        "The quality is okay, but it's way too expensive for what you get.",
    ]

    print("=" * 80)
    print("ENHANCED SENTIMENT ANALYSIS - TEST RESULTS")
    print("=" * 80)

    for i, text in enumerate(test_texts, 1):
        print(f"\n{i}. Text: {text}")
        print("-" * 80)

        result = analyze_text(text)

        print(f"Overall Sentiment: {result['overall_sentiment']} (confidence: {result['overall_confidence']:.2f})")
        print(f"Intensity: {result['intensity']:.2f}")
        print(f"Primary Emotion: {result['emotions']['primary_emotion']}")
        print(f"Urgency: {result['urgency_score']:.2f} {'[URGENT]' if result['is_urgent'] else ''}")

        if result['aspects']:
            print("\nAspects:")
            for aspect in result['aspects']:
                print(f"  • {aspect['aspect']}: {aspect['sentiment']} ({aspect['confidence']:.2f})")

        if result['trajectory_indicators']['satisfaction_change'] != 0:
            change = result['trajectory_indicators']['satisfaction_change']
            direction = "↑ improving" if change > 0 else "↓ deteriorating"
            print(f"\nTrajectory: {direction} ({abs(change):.2f})")

    print("\n" + "=" * 80)
