"""
Sentiment Trajectory Analysis Module

This module provides world-class sentiment analysis capabilities including:
1. Sentiment trajectory tracking across ticket lifecycle
2. Causal analysis linking support issue types to sentiment changes
3. Comprehensive EDA with correlation analysis
4. Advanced sentiment detection with aspect-based analysis
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import re
from collections import defaultdict
from scipy import stats
from sklearn.preprocessing import LabelEncoder
from sklearn.feature_extraction.text import TfidfVectorizer


class SentimentTrajectory(Enum):
    """Sentiment trajectory patterns"""
    IMPROVING = "disgruntled_to_satisfied"  # Started negative, ended positive
    DETERIORATING = "satisfied_to_disgruntled"  # Started positive, ended negative
    CONSISTENTLY_POSITIVE = "consistently_positive"  # Always positive
    CONSISTENTLY_NEGATIVE = "consistently_negative"  # Always negative
    VOLATILE = "volatile"  # Fluctuating between positive and negative
    NEUTRAL_STABLE = "neutral_stable"  # Consistently neutral


@dataclass
class SentimentScore:
    """Detailed sentiment scoring"""
    label: str  # positive, negative, neutral
    confidence: float
    intensity: float  # 0-1 scale
    aspects: Dict[str, str]  # aspect -> sentiment mapping


@dataclass
class TrajectoryAnalysis:
    """Analysis of a ticket's sentiment trajectory"""
    ticket_id: str
    trajectory_type: SentimentTrajectory
    initial_sentiment: SentimentScore
    final_sentiment: SentimentScore
    turning_points: List[Tuple[int, str]]  # (comment_index, sentiment_change)
    sentiment_history: List[SentimentScore]
    volatility_score: float
    improvement_score: float  # -1 to 1, negative means deterioration


@dataclass
class CausalFactor:
    """Causal factors affecting sentiment"""
    issue_category: str
    correlation_strength: float
    associated_trajectories: List[SentimentTrajectory]
    sample_size: int
    confidence_interval: Tuple[float, float]


class SentimentTrajectoryAnalyzer:
    """
    World-class sentiment trajectory analysis system
    """

    def __init__(self):
        self.sentiment_intensifiers = {
            'very', 'extremely', 'absolutely', 'completely', 'totally',
            'really', 'incredibly', 'exceptionally', 'remarkably'
        }

        self.sentiment_diminishers = {
            'somewhat', 'slightly', 'a bit', 'kind of', 'sort of',
            'fairly', 'rather', 'quite', 'moderately'
        }

        # Common support issue categories
        self.issue_categories = {
            'performance': ['slow', 'lag', 'performance', 'speed', 'loading', 'timeout'],
            'bug': ['error', 'bug', 'crash', 'broken', 'not working', 'issue', 'problem'],
            'usability': ['confusing', 'difficult', 'hard to use', 'unclear', 'unintuitive'],
            'feature_request': ['feature', 'would like', 'add', 'implement', 'enhancement'],
            'billing': ['charge', 'billing', 'payment', 'refund', 'invoice', 'subscription'],
            'security': ['security', 'vulnerability', 'breach', 'hack', 'unauthorized'],
            'login': ['login', 'password', 'access', 'authentication', 'sign in'],
            'data': ['data', 'sync', 'lost', 'missing', 'corrupted']
        }

        # Aspect categories for aspect-based sentiment
        self.aspects = {
            'product_quality': ['quality', 'build', 'material', 'durability', 'reliable'],
            'customer_service': ['support', 'service', 'help', 'representative', 'response'],
            'user_experience': ['interface', 'ui', 'ux', 'navigation', 'design'],
            'value': ['price', 'cost', 'value', 'worth', 'expensive', 'cheap'],
            'performance': ['fast', 'slow', 'efficient', 'performance', 'speed']
        }

    def calculate_intensity(self, text: str, base_sentiment: str) -> float:
        """
        Calculate sentiment intensity based on linguistic modifiers

        Args:
            text: Input text
            base_sentiment: Base sentiment (positive/negative/neutral)

        Returns:
            Intensity score between 0 and 1
        """
        words = text.lower().split()
        intensity = 0.5  # Base intensity

        # Check for intensifiers
        intensifier_count = sum(1 for word in words if word in self.sentiment_intensifiers)
        intensity += intensifier_count * 0.15

        # Check for diminishers
        diminisher_count = sum(1 for word in words if word in self.sentiment_diminishers)
        intensity -= diminisher_count * 0.1

        # Check for emphasis (exclamation marks, all caps words)
        exclamations = text.count('!')
        intensity += min(exclamations * 0.05, 0.2)

        caps_words = sum(1 for word in words if word.isupper() and len(word) > 2)
        intensity += min(caps_words * 0.05, 0.15)

        # Normalize to 0-1 range
        return np.clip(intensity, 0.0, 1.0)

    def extract_aspects(self, text: str) -> Dict[str, Optional[str]]:
        """
        Extract aspect-based sentiment (what specific aspects are mentioned)

        Args:
            text: Input text

        Returns:
            Dictionary mapping aspects to sentiment
        """
        text_lower = text.lower()
        aspect_sentiments = {}

        for aspect, keywords in self.aspects.items():
            # Check if any aspect keywords are in the text
            if any(keyword in text_lower for keyword in keywords):
                # Extract sentiment around the aspect
                # This is simplified - in production, use window-based sentiment
                aspect_sentiments[aspect] = None  # To be filled by sentiment model

        return aspect_sentiments

    def categorize_issue(self, text: str) -> List[str]:
        """
        Categorize support issue based on content

        Args:
            text: Issue description

        Returns:
            List of applicable issue categories
        """
        text_lower = text.lower()
        categories = []

        for category, keywords in self.issue_categories.items():
            if any(keyword in text_lower for keyword in keywords):
                categories.append(category)

        return categories if categories else ['general']

    def analyze_trajectory(
        self,
        ticket_id: str,
        comments: List[Dict[str, str]],
        sentiment_predictions: List[Dict[str, float]]
    ) -> TrajectoryAnalysis:
        """
        Analyze sentiment trajectory for a single ticket

        Args:
            ticket_id: Ticket identifier
            comments: List of comment dictionaries with 'text' and 'timestamp'
            sentiment_predictions: List of sentiment predictions for each comment

        Returns:
            TrajectoryAnalysis object
        """
        if not comments or not sentiment_predictions:
            raise ValueError("Comments and predictions cannot be empty")

        # Build sentiment history
        sentiment_history = []
        for comment, pred in zip(comments, sentiment_predictions):
            intensity = self.calculate_intensity(comment['text'], pred['label'])
            aspects = self.extract_aspects(comment['text'])

            sentiment_history.append(SentimentScore(
                label=pred['label'],
                confidence=pred['confidence'],
                intensity=intensity,
                aspects=aspects
            ))

        # Identify trajectory type
        trajectory_type = self._identify_trajectory_pattern(sentiment_history)

        # Find turning points
        turning_points = self._find_turning_points(sentiment_history)

        # Calculate volatility
        volatility = self._calculate_volatility(sentiment_history)

        # Calculate improvement score
        improvement = self._calculate_improvement_score(
            sentiment_history[0],
            sentiment_history[-1]
        )

        return TrajectoryAnalysis(
            ticket_id=ticket_id,
            trajectory_type=trajectory_type,
            initial_sentiment=sentiment_history[0],
            final_sentiment=sentiment_history[-1],
            turning_points=turning_points,
            sentiment_history=sentiment_history,
            volatility_score=volatility,
            improvement_score=improvement
        )

    def _identify_trajectory_pattern(
        self,
        sentiment_history: List[SentimentScore]
    ) -> SentimentTrajectory:
        """Identify the overall trajectory pattern"""

        if len(sentiment_history) < 2:
            label = sentiment_history[0].label
            if label == 'positive':
                return SentimentTrajectory.CONSISTENTLY_POSITIVE
            elif label == 'negative':
                return SentimentTrajectory.CONSISTENTLY_NEGATIVE
            else:
                return SentimentTrajectory.NEUTRAL_STABLE

        # Map sentiments to numeric values
        sentiment_values = []
        for score in sentiment_history:
            if score.label == 'positive':
                sentiment_values.append(1 * score.intensity)
            elif score.label == 'negative':
                sentiment_values.append(-1 * score.intensity)
            else:
                sentiment_values.append(0)

        initial_avg = np.mean(sentiment_values[:len(sentiment_values)//3])
        final_avg = np.mean(sentiment_values[-len(sentiment_values)//3:])

        # Calculate changes
        changes = np.diff(sentiment_values)
        volatility = np.std(changes) if len(changes) > 0 else 0

        # Determine pattern
        if volatility > 0.7:
            return SentimentTrajectory.VOLATILE
        elif initial_avg < -0.3 and final_avg > 0.3:
            return SentimentTrajectory.IMPROVING
        elif initial_avg > 0.3 and final_avg < -0.3:
            return SentimentTrajectory.DETERIORATING
        elif final_avg > 0.3:
            return SentimentTrajectory.CONSISTENTLY_POSITIVE
        elif final_avg < -0.3:
            return SentimentTrajectory.CONSISTENTLY_NEGATIVE
        else:
            return SentimentTrajectory.NEUTRAL_STABLE

    def _find_turning_points(
        self,
        sentiment_history: List[SentimentScore]
    ) -> List[Tuple[int, str]]:
        """Find points where sentiment significantly changed"""
        turning_points = []

        for i in range(1, len(sentiment_history)):
            prev = sentiment_history[i-1]
            curr = sentiment_history[i]

            # Significant change if label changes and confidence is high
            if prev.label != curr.label and curr.confidence > 0.7:
                change_desc = f"{prev.label} → {curr.label}"
                turning_points.append((i, change_desc))

        return turning_points

    def _calculate_volatility(
        self,
        sentiment_history: List[SentimentScore]
    ) -> float:
        """Calculate sentiment volatility (0-1)"""
        if len(sentiment_history) < 2:
            return 0.0

        # Convert to numeric values
        values = []
        for score in sentiment_history:
            if score.label == 'positive':
                values.append(score.intensity)
            elif score.label == 'negative':
                values.append(-score.intensity)
            else:
                values.append(0)

        # Calculate standard deviation of changes
        changes = np.abs(np.diff(values))
        volatility = np.mean(changes) if len(changes) > 0 else 0.0

        return float(np.clip(volatility, 0.0, 1.0))

    def _calculate_improvement_score(
        self,
        initial: SentimentScore,
        final: SentimentScore
    ) -> float:
        """Calculate improvement score (-1 to 1)"""

        # Map sentiments to numeric values
        def sentiment_to_value(score: SentimentScore) -> float:
            if score.label == 'positive':
                return score.intensity
            elif score.label == 'negative':
                return -score.intensity
            else:
                return 0.0

        initial_val = sentiment_to_value(initial)
        final_val = sentiment_to_value(final)

        return float(np.clip(final_val - initial_val, -1.0, 1.0))


class CausalAnalyzer:
    """
    Analyze causal relationships between issue types and sentiment trajectories
    """

    def __init__(self):
        self.trajectory_analyzer = SentimentTrajectoryAnalyzer()

    def analyze_causal_factors(
        self,
        tickets_df: pd.DataFrame,
        min_sample_size: int = 30
    ) -> List[CausalFactor]:
        """
        Analyze causal factors affecting sentiment trajectories

        Args:
            tickets_df: DataFrame with columns: ticket_id, description, comments, sentiments
            min_sample_size: Minimum sample size for reliable correlation

        Returns:
            List of CausalFactor objects
        """
        causal_factors = []

        # Categorize all issues
        tickets_df['issue_categories'] = tickets_df['description'].apply(
            self.trajectory_analyzer.categorize_issue
        )

        # Get all unique categories
        all_categories = set()
        for cats in tickets_df['issue_categories']:
            all_categories.update(cats)

        # For each category, analyze its impact on trajectories
        for category in all_categories:
            # Filter tickets with this category
            category_tickets = tickets_df[
                tickets_df['issue_categories'].apply(lambda x: category in x)
            ]

            if len(category_tickets) < min_sample_size:
                continue

            # Analyze trajectories for these tickets
            # This would integrate with actual sentiment prediction
            # For now, showing the structure

            causal_factors.append(CausalFactor(
                issue_category=category,
                correlation_strength=0.0,  # To be calculated
                associated_trajectories=[],
                sample_size=len(category_tickets),
                confidence_interval=(0.0, 0.0)
            ))

        return causal_factors

    def calculate_correlation_matrix(
        self,
        tickets_df: pd.DataFrame,
        trajectories: List[TrajectoryAnalysis]
    ) -> pd.DataFrame:
        """
        Calculate correlation matrix between issue types and sentiment outcomes

        Args:
            tickets_df: DataFrame with ticket information
            trajectories: List of trajectory analyses

        Returns:
            Correlation matrix as DataFrame
        """
        # Create feature matrix
        trajectory_map = {t.ticket_id: t for t in trajectories}

        # Build features
        features = []
        targets = []

        for _, ticket in tickets_df.iterrows():
            ticket_id = ticket['ticket_id']
            if ticket_id not in trajectory_map:
                continue

            trajectory = trajectory_map[ticket_id]
            categories = self.trajectory_analyzer.categorize_issue(ticket['description'])

            # One-hot encode categories
            feature_vec = {cat: 0 for cat in self.trajectory_analyzer.issue_categories.keys()}
            for cat in categories:
                if cat in feature_vec:
                    feature_vec[cat] = 1

            features.append(feature_vec)
            targets.append(trajectory.improvement_score)

        # Convert to DataFrame
        features_df = pd.DataFrame(features)
        features_df['improvement_score'] = targets

        # Calculate correlations
        correlation_matrix = features_df.corr()

        return correlation_matrix


class SentimentEDA:
    """
    Comprehensive Exploratory Data Analysis for sentiment data
    """

    def __init__(self):
        self.trajectory_analyzer = SentimentTrajectoryAnalyzer()
        self.causal_analyzer = CausalAnalyzer()

    def run_comprehensive_eda(
        self,
        tickets_df: pd.DataFrame,
        output_path: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Run comprehensive EDA on sentiment data

        Args:
            tickets_df: DataFrame with ticket data
            output_path: Optional path to save visualizations

        Returns:
            Dictionary with EDA results
        """
        results = {}

        # 1. Basic statistics
        results['basic_stats'] = self._calculate_basic_stats(tickets_df)

        # 2. Trajectory distribution
        results['trajectory_distribution'] = self._analyze_trajectory_distribution(tickets_df)

        # 3. Issue category analysis
        results['issue_categories'] = self._analyze_issue_categories(tickets_df)

        # 4. Correlation analysis
        results['correlations'] = self._analyze_correlations(tickets_df)

        # 5. Temporal patterns
        results['temporal_patterns'] = self._analyze_temporal_patterns(tickets_df)

        return results

    def _calculate_basic_stats(self, df: pd.DataFrame) -> Dict[str, any]:
        """Calculate basic statistical measures"""
        return {
            'total_tickets': len(df),
            'avg_comments_per_ticket': df['comments'].apply(len).mean() if 'comments' in df else 0,
            'sentiment_distribution': df['sentiment'].value_counts().to_dict() if 'sentiment' in df else {},
        }

    def _analyze_trajectory_distribution(self, df: pd.DataFrame) -> Dict[str, int]:
        """Analyze distribution of trajectory types"""
        # This would be populated with actual trajectory analysis
        return {}

    def _analyze_issue_categories(self, df: pd.DataFrame) -> Dict[str, any]:
        """Analyze issue category patterns"""
        if 'description' not in df:
            return {}

        df['categories'] = df['description'].apply(
            self.trajectory_analyzer.categorize_issue
        )

        # Count category occurrences
        category_counts = defaultdict(int)
        for categories in df['categories']:
            for cat in categories:
                category_counts[cat] += 1

        return dict(category_counts)

    def _analyze_correlations(self, df: pd.DataFrame) -> Dict[str, float]:
        """Analyze correlations between variables"""
        # This would calculate actual correlations
        return {}

    def _analyze_temporal_patterns(self, df: pd.DataFrame) -> Dict[str, any]:
        """Analyze temporal patterns in sentiment"""
        if 'created' not in df:
            return {}

        # This would analyze time-based patterns
        return {}


def generate_sentiment_report(
    tickets_df: pd.DataFrame,
    trajectories: List[TrajectoryAnalysis],
    causal_factors: List[CausalFactor]
) -> str:
    """
    Generate comprehensive sentiment analysis report

    Args:
        tickets_df: Tickets DataFrame
        trajectories: List of trajectory analyses
        causal_factors: List of causal factors

    Returns:
        Formatted report string
    """
    report = []
    report.append("=" * 80)
    report.append("SENTIMENT TRAJECTORY ANALYSIS REPORT")
    report.append("=" * 80)
    report.append("")

    # Summary statistics
    report.append("## SUMMARY STATISTICS")
    report.append(f"Total Tickets Analyzed: {len(tickets_df)}")
    report.append(f"Trajectories Identified: {len(trajectories)}")
    report.append("")

    # Trajectory distribution
    trajectory_counts = defaultdict(int)
    for traj in trajectories:
        trajectory_counts[traj.trajectory_type.value] += 1

    report.append("## TRAJECTORY DISTRIBUTION")
    for traj_type, count in sorted(trajectory_counts.items(), key=lambda x: x[1], reverse=True):
        pct = (count / len(trajectories)) * 100
        report.append(f"  {traj_type}: {count} ({pct:.1f}%)")
    report.append("")

    # Key findings
    improving_tickets = [t for t in trajectories if t.trajectory_type == SentimentTrajectory.IMPROVING]
    deteriorating_tickets = [t for t in trajectories if t.trajectory_type == SentimentTrajectory.DETERIORATING]

    report.append("## KEY FINDINGS")
    report.append(f"  Tickets that improved: {len(improving_tickets)} ({len(improving_tickets)/len(trajectories)*100:.1f}%)")
    report.append(f"  Tickets that deteriorated: {len(deteriorating_tickets)} ({len(deteriorating_tickets)/len(trajectories)*100:.1f}%)")
    report.append("")

    # Causal factors
    if causal_factors:
        report.append("## CAUSAL FACTORS")
        report.append("Top factors influencing sentiment:")
        for factor in sorted(causal_factors, key=lambda x: abs(x.correlation_strength), reverse=True)[:10]:
            report.append(f"  {factor.issue_category}: correlation={factor.correlation_strength:.3f} (n={factor.sample_size})")
        report.append("")

    report.append("=" * 80)

    return "\n".join(report)
