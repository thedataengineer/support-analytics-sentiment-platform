from fastapi import APIRouter, HTTPException, Query
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import duckdb
import numpy as np
from storage.duckdb_client import DuckDBClient

router = APIRouter()
db_client = DuckDBClient()

@router.get("/heatmap")
async def get_sentiment_heatmap(
    x_axis: str = Query("department", description="X-axis dimension"),
    y_axis: str = Query("week", description="Y-axis dimension"),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> Dict[str, Any]:
    """Get sentiment heatmap data"""
    try:
        conn = db_client.get_connection()
        
        # Build date filter
        date_filter = ""
        if start_date and end_date:
            date_filter = f"AND t.created_date BETWEEN '{start_date}' AND '{end_date}'"
        
        # Get heatmap data
        query = f"""
        SELECT 
            t.department,
            strftime('%Y-W%W', t.created_date) as week,
            AVG(sr.sentiment_score) as avg_sentiment,
            COUNT(*) as ticket_count
        FROM tickets t
        LEFT JOIN sentiment_results sr ON t.ticket_id = sr.ticket_id
        WHERE sr.sentiment_score IS NOT NULL {date_filter}
        GROUP BY t.department, week
        ORDER BY department, week
        """
        
        result = conn.execute(query).fetchall()
        
        # Transform to heatmap format
        heatmap_data = []
        for row in result:
            heatmap_data.append({
                "x": row[0],  # department
                "y": row[1],  # week
                "value": round(row[2], 2),  # avg_sentiment
                "count": row[3]  # ticket_count
            })
        
        return {
            "data": heatmap_data,
            "x_axis": x_axis,
            "y_axis": y_axis
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch heatmap data: {str(e)}")

@router.get("/entities")
async def get_entity_analysis(limit: int = Query(50, description="Max entities to return")) -> Dict[str, Any]:
    """Get entity word cloud data"""
    try:
        conn = db_client.get_connection()
        
        # Get entity frequency data
        result = conn.execute("""
            SELECT 
                entity_text,
                entity_type,
                COUNT(*) as frequency,
                AVG(sr.sentiment_score) as avg_sentiment
            FROM entities e
            LEFT JOIN sentiment_results sr ON e.ticket_id = sr.ticket_id
            WHERE entity_text IS NOT NULL
            GROUP BY entity_text, entity_type
            ORDER BY frequency DESC
            LIMIT ?
        """, [limit]).fetchall()
        
        entities = []
        for row in result:
            entities.append({
                "text": row[0],
                "type": row[1],
                "frequency": row[2],
                "sentiment": round(row[3], 2) if row[3] else 0,
                "size": min(max(row[2] * 2, 12), 48)  # Scale font size
            })
        
        return {"entities": entities}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch entity data: {str(e)}")

@router.get("/correlations")
async def get_correlation_matrix() -> Dict[str, Any]:
    """Get feature correlation matrix"""
    try:
        conn = db_client.get_connection()
        
        # Get correlation data
        result = conn.execute("""
            SELECT 
                t.priority,
                t.department,
                sr.sentiment_score,
                EXTRACT(HOUR FROM t.created_date) as hour_created,
                CASE 
                    WHEN t.status = 'Resolved' THEN 1 
                    ELSE 0 
                END as is_resolved
            FROM tickets t
            LEFT JOIN sentiment_results sr ON t.ticket_id = sr.ticket_id
            WHERE sr.sentiment_score IS NOT NULL
        """).fetchall()
        
        # Mock correlation matrix (in production, calculate actual correlations)
        correlations = [
            {"x": "Priority", "y": "Sentiment", "value": -0.45},
            {"x": "Priority", "y": "Resolution", "value": 0.32},
            {"x": "Priority", "y": "Hour", "value": 0.12},
            {"x": "Sentiment", "y": "Priority", "value": -0.45},
            {"x": "Sentiment", "y": "Resolution", "value": 0.67},
            {"x": "Sentiment", "y": "Hour", "value": -0.23},
            {"x": "Resolution", "y": "Priority", "value": 0.32},
            {"x": "Resolution", "y": "Sentiment", "value": 0.67},
            {"x": "Resolution", "y": "Hour", "value": -0.15},
            {"x": "Hour", "y": "Priority", "value": 0.12},
            {"x": "Hour", "y": "Sentiment", "value": -0.23},
            {"x": "Hour", "y": "Resolution", "value": -0.15}
        ]
        
        return {
            "correlations": correlations,
            "features": ["Priority", "Sentiment", "Resolution", "Hour"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch correlation data: {str(e)}")

@router.get("/flow")
async def get_sentiment_flow() -> Dict[str, Any]:
    """Get sentiment flow diagram data"""
    try:
        conn = db_client.get_connection()
        
        # Mock flow data (in production, track actual ticket journey)
        flow_data = {
            "nodes": [
                {"id": "new_positive", "label": "New (Positive)", "value": 150, "sentiment": "positive"},
                {"id": "new_neutral", "label": "New (Neutral)", "value": 200, "sentiment": "neutral"},
                {"id": "new_negative", "label": "New (Negative)", "value": 100, "sentiment": "negative"},
                {"id": "response_positive", "label": "First Response (Positive)", "value": 180, "sentiment": "positive"},
                {"id": "response_neutral", "label": "First Response (Neutral)", "value": 170, "sentiment": "neutral"},
                {"id": "response_negative", "label": "First Response (Negative)", "value": 80, "sentiment": "negative"},
                {"id": "resolved_positive", "label": "Resolved (Positive)", "value": 160, "sentiment": "positive"},
                {"id": "resolved_neutral", "label": "Resolved (Neutral)", "value": 140, "sentiment": "neutral"},
                {"id": "resolved_negative", "label": "Resolved (Negative)", "value": 60, "sentiment": "negative"}
            ],
            "links": [
                {"source": "new_positive", "target": "response_positive", "value": 120},
                {"source": "new_positive", "target": "response_neutral", "value": 20},
                {"source": "new_positive", "target": "response_negative", "value": 10},
                {"source": "new_neutral", "target": "response_positive", "value": 40},
                {"source": "new_neutral", "target": "response_neutral", "value": 130},
                {"source": "new_neutral", "target": "response_negative", "value": 30},
                {"source": "new_negative", "target": "response_positive", "value": 20},
                {"source": "new_negative", "target": "response_neutral", "value": 20},
                {"source": "new_negative", "target": "response_negative", "value": 60}
            ]
        }
        
        return flow_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch flow data: {str(e)}")

@router.get("/anomalies")
async def get_anomaly_alerts() -> Dict[str, Any]:
    """Get anomaly detection alerts"""
    try:
        conn = db_client.get_connection()
        
        # Get recent sentiment trends for anomaly detection
        result = conn.execute("""
            SELECT 
                DATE(t.created_date) as date,
                AVG(sr.sentiment_score) as avg_sentiment,
                COUNT(*) as ticket_count
            FROM tickets t
            LEFT JOIN sentiment_results sr ON t.ticket_id = sr.ticket_id
            WHERE t.created_date >= current_date - interval '30 days'
            AND sr.sentiment_score IS NOT NULL
            GROUP BY DATE(t.created_date)
            ORDER BY date DESC
        """).fetchall()
        
        # Simple anomaly detection (in production, use proper algorithms)
        anomalies = []
        if len(result) > 7:
            recent_avg = sum(row[1] for row in result[:7]) / 7
            for row in result[:7]:
                if abs(row[1] - recent_avg) > 0.3:  # Threshold for anomaly
                    anomalies.append({
                        "date": row[0],
                        "type": "sentiment_spike" if row[1] > recent_avg else "sentiment_drop",
                        "severity": "high" if abs(row[1] - recent_avg) > 0.5 else "medium",
                        "value": round(row[1], 2),
                        "expected": round(recent_avg, 2),
                        "deviation": round(abs(row[1] - recent_avg), 2),
                        "ticket_count": row[2]
                    })
        
        return {"anomalies": anomalies}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch anomaly data: {str(e)}")