from fastapi import APIRouter, HTTPException
from datetime import datetime, timedelta
from typing import Dict, List, Any
import duckdb
from storage.duckdb_client import DuckDBClient

router = APIRouter()
db_client = DuckDBClient()

@router.get("/metrics")
async def get_dashboard_metrics() -> Dict[str, Any]:
    """Get summary metrics for dashboard"""
    try:
        conn = db_client.get_connection()
        
        # Total tickets
        total_tickets = conn.execute("SELECT COUNT(*) FROM tickets").fetchone()[0]
        
        # Average sentiment
        avg_sentiment = conn.execute("""
            SELECT AVG(sentiment_score) 
            FROM sentiment_results 
            WHERE sentiment_score IS NOT NULL
        """).fetchone()[0] or 0
        
        # Processing jobs (mock for now)
        processing_jobs = 0
        
        # Recent trend (last 7 days vs previous 7 days)
        recent_count = conn.execute("""
            SELECT COUNT(*) FROM tickets 
            WHERE created_date >= current_date - interval '7 days'
        """).fetchone()[0]
        
        prev_count = conn.execute("""
            SELECT COUNT(*) FROM tickets 
            WHERE created_date >= current_date - interval '14 days'
            AND created_date < current_date - interval '7 days'
        """).fetchone()[0]
        
        ticket_trend = ((recent_count - prev_count) / max(prev_count, 1)) * 100 if prev_count > 0 else 0
        
        return {
            "total_tickets": total_tickets,
            "avg_sentiment": round(avg_sentiment, 2),
            "processing_jobs": processing_jobs,
            "ticket_trend": round(ticket_trend, 1),
            "sentiment_trend": 0  # Will calculate if needed
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch metrics: {str(e)}")

@router.get("/recent-tickets")
async def get_recent_tickets(limit: int = 10) -> List[Dict[str, Any]]:
    """Get recent tickets with sentiment scores"""
    try:
        conn = db_client.get_connection()
        
        result = conn.execute("""
            SELECT 
                t.ticket_id,
                t.summary,
                t.created_date,
                t.priority,
                t.status,
                sr.sentiment_label,
                sr.sentiment_score
            FROM tickets t
            LEFT JOIN sentiment_results sr ON t.ticket_id = sr.ticket_id
            ORDER BY t.created_date DESC
            LIMIT ?
        """, [limit]).fetchall()
        
        tickets = []
        for row in result:
            tickets.append({
                "ticket_id": row[0],
                "summary": row[1][:100] + "..." if len(row[1]) > 100 else row[1],
                "created_date": row[2],
                "priority": row[3],
                "status": row[4],
                "sentiment_label": row[5] or "Unknown",
                "sentiment_score": round(row[6], 2) if row[6] else 0
            })
        
        return tickets
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch recent tickets: {str(e)}")