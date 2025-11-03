"""
API endpoints for sentiment trajectory analysis
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime
import sys
sys.path.append('../../ml')

from sentiment_trajectory_analysis import (
    SentimentTrajectoryAnalyzer,
    CausalAnalyzer,
    TrajectoryAnalysis,
    CausalFactor
)
from sentiment_model.enhanced_predict import EnhancedSentimentAnalyzer

router = APIRouter(prefix="/api/trajectory", tags=["trajectory"])

# Initialize analyzers
trajectory_analyzer = SentimentTrajectoryAnalyzer()
causal_analyzer = CausalAnalyzer()
sentiment_analyzer = EnhancedSentimentAnalyzer()


class CommentInput(BaseModel):
    """Single comment input"""
    text: str
    timestamp: str
    author: Optional[str] = None


class TicketTrajectoryRequest(BaseModel):
    """Request for analyzing a single ticket's trajectory"""
    ticket_id: str
    description: str
    comments: List[CommentInput]


class TrajectoryAnalysisResponse(BaseModel):
    """Response with trajectory analysis"""
    ticket_id: str
    trajectory_type: str
    initial_sentiment: Dict
    final_sentiment: Dict
    turning_points: List[Dict]
    improvement_score: float
    volatility_score: float
    sentiment_history: List[Dict]
    recommendations: List[str]


class BatchTrajectoryRequest(BaseModel):
    """Request for analyzing multiple tickets"""
    tickets: List[TicketTrajectoryRequest]


class CorrelationAnalysisRequest(BaseModel):
    """Request for correlation analysis"""
    tickets: List[Dict]  # List of ticket data
    min_sample_size: int = 30


class TrajectoryStatsResponse(BaseModel):
    """Overall trajectory statistics"""
    total_tickets: int
    trajectory_distribution: Dict[str, int]
    average_improvement: float
    top_improving_categories: List[Dict]
    top_deteriorating_categories: List[Dict]
    recommendations: List[str]


@router.post("/analyze", response_model=TrajectoryAnalysisResponse)
async def analyze_trajectory(request: TicketTrajectoryRequest):
    """
    Analyze sentiment trajectory for a single ticket

    This endpoint analyzes how sentiment evolves across all comments
    in a ticket's lifecycle, identifying patterns like:
    - Improving (started negative, ended positive)
    - Deteriorating (started positive, ended negative)
    - Volatile (fluctuating)
    - Stable (consistent)
    """
    try:
        # Convert comments to format expected by analyzer
        comments = [
            {
                'text': c.text,
                'timestamp': c.timestamp
            }
            for c in request.comments
        ]

        # Analyze sentiment for each comment
        sentiment_predictions = []
        for comment in comments:
            result = sentiment_analyzer.analyze(comment['text'])
            sentiment_predictions.append({
                'label': result.overall_sentiment,
                'confidence': result.overall_confidence
            })

        # Perform trajectory analysis
        analysis = trajectory_analyzer.analyze_trajectory(
            request.ticket_id,
            comments,
            sentiment_predictions
        )

        # Generate recommendations based on trajectory
        recommendations = _generate_recommendations(analysis, request.description)

        return TrajectoryAnalysisResponse(
            ticket_id=analysis.ticket_id,
            trajectory_type=analysis.trajectory_type.value,
            initial_sentiment={
                'label': analysis.initial_sentiment.label,
                'confidence': analysis.initial_sentiment.confidence,
                'intensity': analysis.initial_sentiment.intensity
            },
            final_sentiment={
                'label': analysis.final_sentiment.label,
                'confidence': analysis.final_sentiment.confidence,
                'intensity': analysis.final_sentiment.intensity
            },
            turning_points=[
                {'index': idx, 'change': change}
                for idx, change in analysis.turning_points
            ],
            improvement_score=analysis.improvement_score,
            volatility_score=analysis.volatility_score,
            sentiment_history=[
                {
                    'label': s.label,
                    'confidence': s.confidence,
                    'intensity': s.intensity
                }
                for s in analysis.sentiment_history
            ],
            recommendations=recommendations
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/analyze-batch")
async def analyze_batch_trajectories(request: BatchTrajectoryRequest):
    """
    Analyze sentiment trajectories for multiple tickets

    Returns aggregate statistics and insights across all tickets.
    """
    try:
        analyses = []

        for ticket_req in request.tickets:
            comments = [
                {'text': c.text, 'timestamp': c.timestamp}
                for c in ticket_req.comments
            ]

            sentiment_predictions = []
            for comment in comments:
                result = sentiment_analyzer.analyze(comment['text'])
                sentiment_predictions.append({
                    'label': result.overall_sentiment,
                    'confidence': result.overall_confidence
                })

            analysis = trajectory_analyzer.analyze_trajectory(
                ticket_req.ticket_id,
                comments,
                sentiment_predictions
            )
            analyses.append(analysis)

        # Calculate aggregate statistics
        stats = _calculate_trajectory_stats(analyses, request.tickets)

        return stats

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch analysis failed: {str(e)}")


@router.post("/correlation-analysis")
async def analyze_correlations(request: CorrelationAnalysisRequest):
    """
    Analyze correlations between issue types and sentiment trajectories

    Identifies which issue categories are most strongly associated with
    sentiment improvements or deteriorations.
    """
    try:
        import pandas as pd

        # Convert to DataFrame
        tickets_df = pd.DataFrame(request.tickets)

        # Perform causal analysis
        causal_factors = causal_analyzer.analyze_causal_factors(
            tickets_df,
            min_sample_size=request.min_sample_size
        )

        # Format response
        response = {
            'total_categories': len(causal_factors),
            'factors': [
                {
                    'category': factor.issue_category,
                    'correlation_strength': factor.correlation_strength,
                    'sample_size': factor.sample_size,
                    'confidence_interval': factor.confidence_interval,
                    'associated_trajectories': [
                        traj.value for traj in factor.associated_trajectories
                    ]
                }
                for factor in causal_factors
            ]
        }

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Correlation analysis failed: {str(e)}")


@router.get("/stats")
async def get_trajectory_stats():
    """
    Get overall trajectory statistics from the database

    Returns summary statistics about sentiment trajectories across all tickets.
    """
    # This would query the database for actual statistics
    # For now, returning structure
    return {
        'total_analyzed': 0,
        'trajectory_distribution': {},
        'average_improvement': 0.0,
        'recommendations': []
    }


@router.post("/predict-trajectory")
async def predict_trajectory(ticket_id: str, initial_sentiment: str, issue_category: str):
    """
    Predict likely trajectory based on initial conditions

    Uses historical patterns to predict how a ticket's sentiment is likely to evolve
    based on its initial sentiment and issue category.
    """
    try:
        # This would use a trained model to predict trajectory
        # For now, returning placeholder based on simple rules

        predictions = {
            'ticket_id': ticket_id,
            'predicted_trajectory': 'improving',  # Would be model prediction
            'confidence': 0.75,
            'risk_factors': [],
            'recommended_actions': []
        }

        # Add risk factors based on category
        if issue_category == 'security' and initial_sentiment == 'negative':
            predictions['risk_factors'].append('High priority security issue with negative start')
            predictions['recommended_actions'].append('Escalate to security team immediately')

        if issue_category == 'performance' and initial_sentiment == 'negative':
            predictions['risk_factors'].append('Performance issues tend to frustrate users')
            predictions['recommended_actions'].append('Provide timeline and workarounds quickly')

        return predictions

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


def _generate_recommendations(analysis: TrajectoryAnalysis, description: str) -> List[str]:
    """Generate actionable recommendations based on trajectory analysis"""
    recommendations = []

    # Check trajectory type
    if analysis.trajectory_type.value == 'disgruntled_to_satisfied':
        recommendations.append("✓ Great job! Customer sentiment improved significantly.")
        recommendations.append("Document the resolution approach for future similar cases.")

    elif analysis.trajectory_type.value == 'satisfied_to_disgruntled':
        recommendations.append("⚠ Alert: Customer sentiment deteriorated despite initial satisfaction.")
        recommendations.append("Escalate to supervisor for immediate review.")
        recommendations.append("Consider reaching out proactively to understand concerns.")

    elif analysis.trajectory_type.value == 'consistently_negative':
        recommendations.append("⚠ Persistent negative sentiment detected.")
        recommendations.append("Assign senior support agent if not already done.")
        recommendations.append("Consider offering compensation or escalation to management.")

    elif analysis.trajectory_type.value == 'volatile':
        recommendations.append("⚠ Unstable sentiment trajectory detected.")
        recommendations.append("Customer may be uncertain or receiving inconsistent information.")
        recommendations.append("Ensure clear, consistent communication across all responses.")

    # Check volatility
    if analysis.volatility_score > 0.7:
        recommendations.append("High volatility: Ensure consistent messaging across team members.")

    # Check improvement score
    if analysis.improvement_score < -0.5:
        recommendations.append("Significant deterioration: Requires immediate management attention.")
    elif analysis.improvement_score > 0.5:
        recommendations.append("Excellent recovery: Share as a success story with the team.")

    # Check for turning points
    if len(analysis.turning_points) > 3:
        recommendations.append("Multiple sentiment changes: Review communication approach.")

    # Issue category specific recommendations
    categories = trajectory_analyzer.categorize_issue(description)
    if 'security' in categories:
        recommendations.append("Security issue: Ensure compliance team is notified.")
    if 'billing' in categories:
        recommendations.append("Billing issue: Fast-track refund if applicable.")
    if 'bug' in categories:
        recommendations.append("Bug reported: Link to engineering ticket for tracking.")

    return recommendations if recommendations else ["Continue monitoring ticket progress."]


def _calculate_trajectory_stats(
    analyses: List[TrajectoryAnalysis],
    tickets: List[TicketTrajectoryRequest]
) -> TrajectoryStatsResponse:
    """Calculate aggregate statistics from multiple analyses"""
    from collections import Counter

    # Count trajectory types
    trajectory_counts = Counter(a.trajectory_type.value for a in analyses)

    # Calculate average improvement
    avg_improvement = sum(a.improvement_score for a in analyses) / len(analyses)

    # Categorize tickets
    improving_tickets = [
        (a, t) for a, t in zip(analyses, tickets)
        if a.improvement_score > 0.3
    ]
    deteriorating_tickets = [
        (a, t) for a, t in zip(analyses, tickets)
        if a.improvement_score < -0.3
    ]

    # Get top categories for improving tickets
    improving_categories = []
    for _, ticket in improving_tickets:
        cats = trajectory_analyzer.categorize_issue(ticket.description)
        improving_categories.extend(cats)

    top_improving = [
        {'category': cat, 'count': count}
        for cat, count in Counter(improving_categories).most_common(5)
    ]

    # Get top categories for deteriorating tickets
    deteriorating_categories = []
    for _, ticket in deteriorating_tickets:
        cats = trajectory_analyzer.categorize_issue(ticket.description)
        deteriorating_categories.extend(cats)

    top_deteriorating = [
        {'category': cat, 'count': count}
        for cat, count in Counter(deteriorating_categories).most_common(5)
    ]

    # Generate recommendations
    recommendations = []
    if len(improving_tickets) / len(analyses) > 0.5:
        recommendations.append("✓ Over 50% of tickets show sentiment improvement - great work!")
    if len(deteriorating_tickets) / len(analyses) > 0.2:
        recommendations.append("⚠ More than 20% of tickets deteriorating - review support processes")

    return TrajectoryStatsResponse(
        total_tickets=len(analyses),
        trajectory_distribution=dict(trajectory_counts),
        average_improvement=avg_improvement,
        top_improving_categories=top_improving,
        top_deteriorating_categories=top_deteriorating,
        recommendations=recommendations
    )
