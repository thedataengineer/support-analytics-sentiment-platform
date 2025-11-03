import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import os
from datetime import datetime, timedelta
import io
from storage.storage_manager import StorageManager

def generate_pdf_report(start_date: str, end_date: str) -> str:
    """
    Generate PDF report with sentiment analysis summary
    """
    # Create reports directory if it doesn't exist
    reports_dir = "reports"
    os.makedirs(reports_dir, exist_ok=True)

    filename = f"{reports_dir}/sentiment_report_{start_date}_to_{end_date}.pdf"
    doc = SimpleDocTemplate(filename, pagesize=letter)
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
    )

    story = []

    # Title
    story.append(Paragraph("Sentiment Analysis Report", title_style))
    story.append(Spacer(1, 12))

    # Date range
    story.append(Paragraph(f"Period: {start_date} to {end_date}", styles['Normal']))
    story.append(Spacer(1, 12))

    # Executive Summary
    story.append(Paragraph("Executive Summary", styles['Heading2']))
    story.append(Paragraph(
        "This report provides an overview of customer sentiment analysis "
        "based on recent feedback data. The analysis covers positive, negative, "
        "and neutral sentiments across the specified time period.",
        styles['Normal']
    ))
    story.append(Spacer(1, 24))

    # Query real data from DuckDB
    storage = StorageManager()
    try:
        # Query sentiment distribution
        query = f"""
        SELECT sentiment, COUNT(*) as count
        FROM sentiment_results 
        WHERE comment_timestamp >= '{start_date}' 
        AND comment_timestamp <= '{end_date}'
        GROUP BY sentiment
        """
        
        distribution = storage.duckdb_client.execute_query(query)
        
        sentiment_data = {"positive": 0, "negative": 0, "neutral": 0}
        for row in distribution:
            sentiment_data[row[0]] = row[1]

        # Get total count of records
        total_count = sum(sentiment_data.values())

        story.append(Paragraph("Summary Statistics", styles['Heading3']))
        story.append(Paragraph(f"Total feedback records analyzed: {total_count:,}", styles['Normal']))
        story.append(Paragraph(f"Positive: {sentiment_data['positive']:,} ({sentiment_data['positive']/total_count*100:.1f}%)" if total_count > 0 else "Positive: 0 (0.0%)", styles['Normal']))
        story.append(Paragraph(f"Negative: {sentiment_data['negative']:,} ({sentiment_data['negative']/total_count*100:.1f}%)" if total_count > 0 else "Negative: 0 (0.0%)", styles['Normal']))
        story.append(Paragraph(f"Neutral: {sentiment_data['neutral']:,} ({sentiment_data['neutral']/total_count*100:.1f}%)" if total_count > 0 else "Neutral: 0 (0.0%)", styles['Normal']))
        story.append(Spacer(1, 24))

    except Exception as e:
        print(f"Error querying sentiment data: {e}")
        sentiment_data = {"positive": 0, "negative": 0, "neutral": 0}
        total_count = 0

    # Generate and add chart
    chart_path = generate_sentiment_chart(sentiment_data, start_date, end_date)
    if chart_path:
        story.append(Paragraph("Sentiment Distribution", styles['Heading3']))
        story.append(Image(chart_path, 6*inch, 4*inch))
        story.append(Spacer(1, 12))

    # Build PDF
    doc.build(story)

    # Clean up chart file
    if chart_path and os.path.exists(chart_path):
        os.remove(chart_path)

    return filename

def generate_sentiment_chart(sentiment_data: dict, start_date: str, end_date: str) -> str:
    """
    Generate pie chart for sentiment distribution
    """
    try:
        labels = sentiment_data.keys()
        sizes = sentiment_data.values()
        colors_list = ['#4CAF50', '#F44336', '#FFC107']  # green, red, yellow

        fig, ax = plt.subplots()
        ax.pie(sizes, labels=labels, colors=colors_list, autopct='%1.1f%%', startangle=90)
        ax.axis('equal')
        ax.set_title(f'Sentiment Distribution\n{start_date} to {end_date}')

        chart_path = f"temp_chart_{datetime.now().timestamp()}.png"
        plt.savefig(chart_path)
        plt.close()

        return chart_path
    except Exception as e:
        print(f"Error generating chart: {e}")
        return None
