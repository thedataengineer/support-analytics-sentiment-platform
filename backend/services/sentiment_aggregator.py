"""
Sentiment Aggregator - Calculates ultimate sentiment from comment timeline
"""
from typing import List, Dict, Tuple
import logging

logger = logging.getLogger(__name__)


class SentimentAggregator:
    """Calculate ultimate sentiment from a series of sentiment results"""

    # Sentiment scores for aggregation
    SENTIMENT_SCORES = {
        'positive': 1.0,
        'neutral': 0.0,
        'negative': -1.0
    }

    @classmethod
    def calculate_ultimate(cls, sentiments: List[Dict], strategy: str = 'weighted_recent') -> Tuple[str, float, str]:
        """
        Calculate ultimate sentiment from list of sentiment results

        Args:
            sentiments: List of dicts with 'sentiment', 'confidence', 'comment_number' keys
                       Should be sorted by comment_number (chronological)
            strategy: 'latest', 'weighted_recent', 'trajectory'

        Returns:
            (sentiment, confidence, trend) tuple
        """
        if not sentiments:
            return 'neutral', 0.5, 'stable'

        if strategy == 'latest':
            return cls._calculate_latest(sentiments)
        elif strategy == 'weighted_recent':
            return cls._calculate_weighted_recent(sentiments)
        elif strategy == 'trajectory':
            return cls._calculate_trajectory(sentiments)
        else:
            return cls._calculate_weighted_recent(sentiments)

    @classmethod
    def _calculate_latest(cls, sentiments: List[Dict]) -> Tuple[str, float, str]:
        """Use the most recent comment's sentiment"""
        # Sentiments should already be sorted by comment_number
        latest = sentiments[-1]

        # Calculate trend from last few comments
        trend = cls._calculate_trend(sentiments)

        return latest['sentiment'], latest['confidence'], trend

    @classmethod
    def _calculate_weighted_recent(cls, sentiments: List[Dict]) -> Tuple[str, float, str]:
        """Weighted average of recent comments (last 5, with recent having more weight)"""
        # Take last 5 comments or all if less than 5
        recent = sentiments[-5:]

        if not recent:
            return 'neutral', 0.5, 'stable'

        # Weight: more recent = more weight (1, 2, 3, 4, 5)
        weights = list(range(1, len(recent) + 1))
        total_weight = sum(weights)

        # Calculate weighted score
        weighted_score = 0.0
        weighted_confidence = 0.0

        for weight, s in zip(weights, recent):
            score = cls.SENTIMENT_SCORES.get(s['sentiment'], 0.0)
            weighted_score += score * weight * s['confidence']
            weighted_confidence += s['confidence'] * weight

        avg_score = weighted_score / total_weight
        avg_confidence = weighted_confidence / total_weight

        # Map score back to sentiment
        if avg_score > 0.2:
            sentiment = 'positive'
        elif avg_score < -0.2:
            sentiment = 'negative'
        else:
            sentiment = 'neutral'

        trend = cls._calculate_trend(sentiments)

        return sentiment, round(avg_confidence, 3), trend

    @classmethod
    def _calculate_trajectory(cls, sentiments: List[Dict]) -> Tuple[str, float, str]:
        """Calculate based on sentiment trajectory (improving vs declining)"""
        if len(sentiments) < 2:
            s = sentiments[0]
            return s['sentiment'], s['confidence'], 'stable'

        # Split into first half and second half
        mid = len(sentiments) // 2
        first_half = sentiments[:mid]
        second_half = sentiments[mid:]

        def avg_score(sents):
            if not sents:
                return 0.0
            scores = [cls.SENTIMENT_SCORES.get(s['sentiment'], 0.0) * s['confidence'] for s in sents]
            return sum(scores) / len(scores)

        first_avg = avg_score(first_half)
        second_avg = avg_score(second_half)

        # Determine trajectory
        if second_avg > first_avg + 0.2:
            trend = 'improving'
            sentiment = 'positive'
        elif second_avg < first_avg - 0.2:
            trend = 'declining'
            sentiment = 'negative'
        else:
            trend = 'stable'
            # Use most recent
            sentiment = sentiments[-1]['sentiment']

        avg_confidence = sum(s['confidence'] for s in sentiments) / len(sentiments)

        return sentiment, round(avg_confidence, 3), trend

    @classmethod
    def _calculate_trend(cls, sentiments: List[Dict]) -> str:
        """
        Calculate sentiment trend: improving, declining, or stable
        Compares first half vs second half of comments
        """
        if len(sentiments) < 2:
            return 'stable'

        mid = len(sentiments) // 2
        if mid == 0:
            return 'stable'

        first_half = sentiments[:mid]
        second_half = sentiments[mid:]

        def avg_score(sents):
            if not sents:
                return 0.0
            scores = [cls.SENTIMENT_SCORES.get(s['sentiment'], 0.0) for s in sents]
            return sum(scores) / len(scores)

        first_avg = avg_score(first_half)
        second_avg = avg_score(second_half)

        if second_avg > first_avg + 0.3:
            return 'improving'
        elif second_avg < first_avg - 0.3:
            return 'declining'
        else:
            return 'stable'
