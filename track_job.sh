#!/bin/bash

JOB_ID=${1:-"064d2288-7cfd-4de6-b256-ed54ef62f614"}
API_BASE="http://sentiment-platform-demo-110240311.us-east-1.elb.amazonaws.com"

echo "Tracking job: $JOB_ID"
echo "Press Ctrl+C to stop"
echo

while true; do
    RESPONSE=$(curl -s "$API_BASE/api/job/$JOB_ID")
    STATUS=$(echo $RESPONSE | jq -r '.status')
    PROCESSED=$(echo $RESPONSE | jq -r '.records_processed // 0')
    SENTIMENT=$(echo $RESPONSE | jq -r '.sentiment_records // 0')
    ENTITIES=$(echo $RESPONSE | jq -r '.entity_records // 0')
    ERROR=$(echo $RESPONSE | jq -r '.error // "none"')
    FILENAME=$(echo $RESPONSE | jq -r '.file_name // "unknown"')
    FILESIZE=$(echo $RESPONSE | jq -r '.file_size // 0')
    STARTED=$(echo $RESPONSE | jq -r '.started_at // "not started"')
    DURATION=$(echo $RESPONSE | jq -r '.duration // 0')
    
    # Calculate rates if processing
    if [ "$PROCESSED" -gt 0 ] && [ "$DURATION" != "0" ] && [ "$DURATION" != "null" ]; then
        RATE=$(echo "scale=1; $PROCESSED / $DURATION" | bc -l 2>/dev/null || echo "0")
    else
        RATE="0"
    fi
    
    clear
    echo "=== JOB PROGRESS: $JOB_ID ==="
    echo "File: $FILENAME ($(echo "scale=1; $FILESIZE / 1024 / 1024" | bc -l 2>/dev/null || echo "0")MB)"
    echo "Status: $STATUS"
    echo "Started: $STARTED"
    echo
    echo "📊 PROCESSING STATS:"
    echo "  Records Processed: $PROCESSED"
    echo "  Processing Rate: $RATE records/sec"
    echo "  Sentiment Records: $SENTIMENT"
    echo "  Entity Records: $ENTITIES"
    echo "  Duration: ${DURATION}s"
    echo
    if [ "$ERROR" != "none" ] && [ "$ERROR" != "null" ]; then
        echo "❌ Error: $ERROR"
    fi
    
    # Show what's happening based on status
    case "$STATUS" in
        "queued") echo "⏳ Waiting in queue for processing..." ;;
        "running") echo "🔄 Processing tickets and analyzing sentiment..." ;;
        "completed") echo "✅ Processing completed successfully!" ;;
        "failed") echo "❌ Processing failed!" ;;
    esac
    
    echo
    echo "$(date) | Press Ctrl+C to stop monitoring"
    
    if [ "$STATUS" = "completed" ] || [ "$STATUS" = "failed" ]; then
        echo
        echo "Job finished! Final stats above."
        break
    fi
    
    sleep 3
done