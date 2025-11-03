from backend.jobs.ingest_job import process_csv_upload  # Or process_parquet_data if that's the function

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


parquet_path = '/Users/karteek/dev/work/accionlabs/jira-profiler/Jira.parquet'
job_id = 'terminal-test-job-001'

# If there's a process_parquet_data(df, job_id) function, use:
import pandas as pd
df = pd.read_parquet(parquet_path)
from jobs.ingest_job import process_parquet_data 
result = process_parquet_data(df, job_id)
print(result)
