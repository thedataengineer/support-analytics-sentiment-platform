from fastapi import FastAPI
import pandas as pd
from textblob import TextBlob

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Sentiment API"}

@app.post("/ingest-jira")
def ingest_jira():
    df = pd.read_parquet('/Users/karteek/dev/work/accionlabs/jira-profiler/Jira.parquet')
    return {
        "rows": len(df),
        "columns": len(df.columns),
        "sample": df.head(2)['Summary'].tolist()
    }

@app.post("/analyze-sentiment")
def analyze_sentiment():
    df = pd.read_parquet('/Users/karteek/dev/work/accionlabs/jira-profiler/Jira.parquet')
    
    # Analyze first 100 rows for speed
    sample_df = df.head(100)
    results = []
    
    for _, row in sample_df.iterrows():
        text = str(row.get('Summary', '')) + ' ' + str(row.get('Description', ''))
        blob = TextBlob(text)
        
        results.append({
            'ticket': row.get('Issue key', 'N/A'),
            'sentiment': 'positive' if blob.sentiment.polarity > 0 else 'negative' if blob.sentiment.polarity < 0 else 'neutral',
            'polarity': round(blob.sentiment.polarity, 3),
            'subjectivity': round(blob.sentiment.subjectivity, 3)
        })
    
    # Summary stats
    sentiments = [r['sentiment'] for r in results]
    summary = {
        'total_analyzed': len(results),
        'positive': sentiments.count('positive'),
        'negative': sentiments.count('negative'),
        'neutral': sentiments.count('neutral')
    }
    
    return {'summary': summary, 'results': results[:10]}