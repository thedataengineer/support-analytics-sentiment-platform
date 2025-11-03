#!/usr/bin/env python3
import pandas as pd
import sys
import os
sys.path.insert(0, 'backend')

from backend.services.column_mapping import ColumnMapper

# Load JIRA parquet
df = pd.read_parquet('/Users/karteek/dev/work/accionlabs/jira-profiler/Jira.parquet')
print(f"Loaded {len(df)} rows, {len(df.columns)} columns")

# Map columns
mapper = ColumnMapper()
mapping = mapper.create_mapping(df.columns.tolist(), 'jira')
print(f"Text columns: {mapping['text_columns'][:3]}...")

# Sample data
sample = df.head(3)[mapping['text_columns'][:2]]
print("\nSample data:")
print(sample)