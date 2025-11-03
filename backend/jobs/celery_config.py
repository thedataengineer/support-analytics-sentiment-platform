from celery import Celery
import os
from dotenv import load_dotenv

load_dotenv()

# Celery configuration
celery_app = Celery(
    'sentiment_platform',
    broker=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
    backend=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
    include=['jobs.ingest_job', 'jobs.parquet_ingest_job', 'jobs.reporting_tasks']
)

# Optional configuration
celery_app.conf.update(
    result_expires=3600,
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

if __name__ == '__main__':
    celery_app.start()
