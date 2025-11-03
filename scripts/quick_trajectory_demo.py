#!/usr/bin/env python3
"""
Quick Demo of Sentiment Trajectory Analysis

This script demonstrates the key capabilities of the sentiment trajectory
analysis system with sample data.
"""

import sys
sys.path.append('../ml')

from sentiment_trajectory_analysis import SentimentTrajectoryAnalyzer
from sentiment_model.enhanced_predict import EnhancedSentimentAnalyzer


def demo_enhanced_sentiment():
    """Demo the enhanced sentiment analyzer"""
    print("=" * 80)
    print("DEMO 1: Enhanced Sentiment Analysis")
    print("=" * 80)

    analyzer = EnhancedSentimentAnalyzer()

    test_cases = [
        "This product is absolutely terrible! Very disappointed.",
        "The customer service was extremely helpful, thank you!",
        "URGENT: System is down, need immediate assistance!",
        "The performance is somewhat slow, but usable.",
        "Great quality and value for money, highly recommend!"
    ]

    for i, text in enumerate(test_cases, 1):
        print(f"\n{i}. Analyzing: \"{text}\"")
        print("-" * 80)

        result = analyzer.analyze(text)

        print(f"   Sentiment: {result.overall_sentiment} (confidence: {result.overall_confidence:.2f})")
        print(f"   Intensity: {result.intensity:.2f}")
        print(f"   Emotion: {result.emotions.primary_emotion} (valence: {result.emotions.valence:+.2f})")
        print(f"   Urgency: {result.urgency_score:.2f} {'⚠ URGENT' if result.is_urgent else ''}")

        if result.aspects:
            print(f"   Aspects detected:")
            for aspect in result.aspects:
                print(f"      • {aspect.aspect}: {aspect.sentiment} ({aspect.confidence:.2f})")


def demo_trajectory_analysis():
    """Demo trajectory analysis"""
    print("\n\n" + "=" * 80)
    print("DEMO 2: Sentiment Trajectory Analysis")
    print("=" * 80)

    trajectory_analyzer = SentimentTrajectoryAnalyzer()
    sentiment_analyzer = EnhancedSentimentAnalyzer()

    # Example: Improving trajectory
    print("\n\nExample 1: IMPROVING Trajectory (Disgruntled → Satisfied)")
    print("-" * 80)

    ticket_id = "TICKET-IMPROVE-001"
    comments = [
        {'text': 'The application is completely broken and unusable!', 'timestamp': '2024-01-01'},
        {'text': 'Still having issues, this is very frustrating', 'timestamp': '2024-01-02'},
        {'text': 'Getting better, but not quite there yet', 'timestamp': '2024-01-03'},
        {'text': 'Much better now, seems to be working', 'timestamp': '2024-01-04'},
        {'text': 'Excellent! Everything is fixed. Thank you so much!', 'timestamp': '2024-01-05'}
    ]

    print(f"Ticket: {ticket_id}")
    print(f"Comments: {len(comments)}")
    print()

    # Analyze each comment
    sentiments = []
    for i, comment in enumerate(comments, 1):
        result = sentiment_analyzer.analyze(comment['text'])
        sentiments.append({
            'label': result.overall_sentiment,
            'confidence': result.overall_confidence
        })
        print(f"  {i}. {comment['timestamp']}: {result.overall_sentiment} ({result.overall_confidence:.2f})")
        print(f"     \"{comment['text'][:60]}...\"")

    # Analyze trajectory
    trajectory = trajectory_analyzer.analyze_trajectory(ticket_id, comments, sentiments)

    print(f"\n📊 Trajectory Analysis:")
    print(f"   Pattern: {trajectory.trajectory_type.value}")
    print(f"   Improvement Score: {trajectory.improvement_score:+.2f} {'✓ POSITIVE' if trajectory.improvement_score > 0 else '✗ NEGATIVE'}")
    print(f"   Volatility: {trajectory.volatility_score:.2f}")
    print(f"   Turning Points: {len(trajectory.turning_points)}")

    if trajectory.turning_points:
        print(f"\n   🔄 Sentiment Changes:")
        for idx, change in trajectory.turning_points:
            print(f"      • At comment {idx}: {change}")

    # Example: Deteriorating trajectory
    print("\n\n" + "-" * 80)
    print("Example 2: DETERIORATING Trajectory (Satisfied → Disgruntled)")
    print("-" * 80)

    ticket_id2 = "TICKET-DEGRADE-001"
    comments2 = [
        {'text': 'Thanks for the quick response, looking forward to the fix', 'timestamp': '2024-01-01'},
        {'text': 'Still waiting, hope it gets resolved soon', 'timestamp': '2024-01-02'},
        {'text': 'This is taking longer than expected', 'timestamp': '2024-01-03'},
        {'text': 'Very disappointed with the delay and lack of updates', 'timestamp': '2024-01-04'},
        {'text': 'Extremely frustrated! This is unacceptable!', 'timestamp': '2024-01-05'}
    ]

    print(f"Ticket: {ticket_id2}")
    print(f"Comments: {len(comments2)}")
    print()

    sentiments2 = []
    for i, comment in enumerate(comments2, 1):
        result = sentiment_analyzer.analyze(comment['text'])
        sentiments2.append({
            'label': result.overall_sentiment,
            'confidence': result.overall_confidence
        })
        print(f"  {i}. {comment['timestamp']}: {result.overall_sentiment} ({result.overall_confidence:.2f})")
        print(f"     \"{comment['text'][:60]}...\"")

    trajectory2 = trajectory_analyzer.analyze_trajectory(ticket_id2, comments2, sentiments2)

    print(f"\n📊 Trajectory Analysis:")
    print(f"   Pattern: {trajectory2.trajectory_type.value}")
    print(f"   Improvement Score: {trajectory2.improvement_score:+.2f} {'✓ POSITIVE' if trajectory2.improvement_score > 0 else '⚠ NEGATIVE'}")
    print(f"   Volatility: {trajectory2.volatility_score:.2f}")

    print(f"\n   💡 Recommendations:")
    recommendations = [
        "⚠ Alert: Customer sentiment deteriorated significantly",
        "→ Immediate escalation to manager required",
        "→ Proactive outreach to address concerns",
        "→ Consider compensation or expedited resolution"
    ]
    for rec in recommendations:
        print(f"      {rec}")


def demo_issue_categorization():
    """Demo issue categorization"""
    print("\n\n" + "=" * 80)
    print("DEMO 3: Issue Categorization & Causal Analysis")
    print("=" * 80)

    analyzer = SentimentTrajectoryAnalyzer()

    test_issues = [
        "The application is very slow and takes forever to load",
        "I found a security vulnerability in the authentication system",
        "Cannot login after resetting my password",
        "The billing shows incorrect charges on my account",
        "The interface is confusing and hard to navigate",
        "Would like to request a new feature for dark mode"
    ]

    print("\nCategorizing support issues:")
    print()

    for issue in test_issues:
        categories = analyzer.categorize_issue(issue)
        print(f"Issue: \"{issue[:60]}...\"")
        print(f"   Categories: {', '.join(categories)}")
        print()

    print("\n📊 Expected Correlation with Sentiment:")
    print("   (Based on typical patterns)")
    print()
    correlations = {
        'performance': -0.45,
        'security': -0.52,
        'login': -0.38,
        'billing': -0.32,
        'usability': -0.28,
        'feature_request': +0.23
    }

    for category, corr in sorted(correlations.items(), key=lambda x: x[1]):
        strength = "Strong" if abs(corr) > 0.5 else "Moderate" if abs(corr) > 0.3 else "Weak"
        direction = "hurts" if corr < 0 else "helps"
        print(f"   {category:18s}: {corr:+.2f}  [{strength:8s}] - {direction} sentiment")


def main():
    """Run all demos"""
    print("\n")
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 15 + "SENTIMENT TRAJECTORY ANALYSIS DEMO" + " " * 29 + "║")
    print("╚" + "═" * 78 + "╝")

    try:
        demo_enhanced_sentiment()
        demo_trajectory_analysis()
        demo_issue_categorization()

        print("\n\n" + "=" * 80)
        print("DEMO COMPLETE")
        print("=" * 80)
        print()
        print("Next Steps:")
        print("  1. Run the Jupyter notebook: jupyter notebook notebooks/sentiment_trajectory_eda.ipynb")
        print("  2. Read the guide: SENTIMENT_TRAJECTORY_GUIDE.md")
        print("  3. Test with your data: Replace sample_data.csv with your Jira export")
        print()
        print("For API usage, see: backend/api/trajectory_api.py")
        print()

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure you're in the scripts directory and dependencies are installed:")
        print("  cd sentiment-platform/scripts")
        print("  pip install -r ../ml/requirements.txt")
        raise


if __name__ == "__main__":
    main()
