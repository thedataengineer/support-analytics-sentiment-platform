#!/bin/bash

# Sentiment Platform Monitor Script

API_BASE="http://sentiment-platform-demo-110240311.us-east-1.elb.amazonaws.com"
CLUSTER="sentiment-platform-demo"
REGION="us-east-1"

show_status() {
    echo "=== PLATFORM STATUS ==="
    echo "Backend: $(curl -s $API_BASE/health | jq -r '.status')"
    echo "Services:"
    aws ecs describe-services --cluster $CLUSTER --services sentiment-platform-demo-backend sentiment-platform-demo-ml sentiment-platform-demo-celery --region $REGION --query 'services[*].{Name:serviceName,Running:runningCount,Desired:desiredCount}' --output table
}

show_jobs() {
    echo "=== RECENT JOBS ==="
    curl -s "$API_BASE/api/jobs?limit=5" | jq -r '.results[] | "\(.job_id) | \(.status) | \(.file_name) | \(.records_processed) records"'
}

tail_logs() {
    SERVICE=$1
    if [ -z "$SERVICE" ]; then
        echo "Available services: backend, ml, celery"
        return
    fi
    
    TASK_ARN=$(aws ecs list-tasks --cluster $CLUSTER --service-name sentiment-platform-demo-$SERVICE --region $REGION --query 'taskArns[0]' --output text)
    
    if [ "$TASK_ARN" != "None" ]; then
        aws logs tail /ecs/sentiment-platform-demo-$SERVICE --follow --region $REGION
    else
        echo "No running tasks for $SERVICE"
    fi
}

case "$1" in
    "status") show_status ;;
    "jobs") show_jobs ;;
    "logs") tail_logs $2 ;;
    "watch") 
        while true; do
            clear
            show_status
            echo
            show_jobs
            sleep 5
        done
        ;;
    *)
        echo "Usage: $0 {status|jobs|logs <service>|watch}"
        echo "Examples:"
        echo "  $0 status     - Show platform status"
        echo "  $0 jobs       - Show recent jobs"
        echo "  $0 logs backend - Tail backend logs"
        echo "  $0 watch      - Live monitoring"
        ;;
esac