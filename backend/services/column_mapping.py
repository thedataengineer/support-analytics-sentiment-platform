import pandas as pd
import json
import os
from typing import Dict, List

class ColumnMapper:
    def __init__(self, mapping_file: str = "column_mappings.json"):
        self.mapping_file = mapping_file
        self.mappings = self.load_mappings()

    def load_mappings(self) -> Dict:
        """Load existing column mappings from file"""
        if os.path.exists(self.mapping_file):
            with open(self.mapping_file, 'r') as f:
                return json.load(f)
        return {}

    def save_mappings(self):
        """Save column mappings to file"""
        with open(self.mapping_file, 'w') as f:
            json.dump(self.mappings, f, indent=2)

    def detect_text_columns(self, df: pd.DataFrame) -> List[str]:
        """Automatically detect potential text columns"""
        text_columns = []
        for col in df.columns:
            # Check if column name suggests text content
            col_lower = col.lower()
            if any(keyword in col_lower for keyword in [
                'summary', 'description', 'comment', 'text', 'message',
                'feedback', 'problem', 'request'
            ]):
                text_columns.append(col)
            # Also check sample data types
            elif df[col].dtype == 'object':
                # Check if column contains text data
                sample = df[col].dropna().head(5)
                if len(sample) > 0 and any(isinstance(val, str) and len(val) > 10 for val in sample):
                    text_columns.append(col)

        return text_columns

    def create_mapping(self, csv_headers: List[str], source_name: str) -> Dict:
        """Create column mapping for a CSV source"""
        detected_text_columns = self.detect_text_columns(pd.DataFrame(columns=csv_headers))
        normalized_headers = {col.lower(): col for col in csv_headers}

        mapping = {
            "source": source_name,
            "headers": csv_headers,
            "text_columns": detected_text_columns,
            "id_column": None,
            "date_column": None
        }

        # Try to detect ID and date columns
        for col in csv_headers:
            col_lower = col.lower()
            if 'id' in col_lower and not mapping["id_column"]:
                mapping["id_column"] = col
            elif any(date_word in col_lower for date_word in ['date', 'created', 'time']):
                mapping["date_column"] = col

        # If we still haven't identified an ID column, fall back to common Jira identifiers
        if not mapping["id_column"]:
            for candidate in ["Issue key", "Issue id", "ticket_id", "Ticket ID", "ID"]:
                if candidate in csv_headers:
                    mapping["id_column"] = candidate
                    break
                lower_candidate = candidate.lower()
                if lower_candidate in normalized_headers:
                    mapping["id_column"] = normalized_headers[lower_candidate]
                    break

        # Ensure key Jira text columns are captured even if automatic detection missed them
        for candidate in ["Summary", "Description", "Comment", "Comments", "Issue summary"]:
            if candidate in csv_headers and candidate not in mapping["text_columns"]:
                mapping["text_columns"].append(candidate)
            else:
                lower_candidate = candidate.lower()
                if lower_candidate in normalized_headers:
                    canonical = normalized_headers[lower_candidate]
                    if canonical not in mapping["text_columns"]:
                        mapping["text_columns"].append(canonical)

        # Deduplicate while preserving order
        seen = set()
        mapping["text_columns"] = [col for col in mapping["text_columns"] if not (col in seen or seen.add(col))]

        # Separate comment columns from text columns
        comment_columns = [col for col in mapping["text_columns"] if col.lower().startswith("comment")]

        # Keep ALL comment columns for separate analysis
        mapping["comment_columns"] = sorted(comment_columns, key=lambda x: (
            # Sort by number in column name for proper chronological order
            int(x.split('.')[-1]) if '.' in x and x.split('.')[-1].isdigit() else 0
        ))

        # For text_columns, keep high-signal fields (Summary, Description)
        preferred = []
        for candidate in ["Summary", "Description", "Parent summary"]:
            if candidate in mapping["text_columns"]:
                preferred.append(candidate)
            else:
                lower_candidate = candidate.lower()
                if lower_candidate in normalized_headers:
                    preferred.append(normalized_headers[lower_candidate])

        if preferred:
            mapping["text_columns"] = preferred

        self.mappings[source_name] = mapping
        self.save_mappings()

        return mapping

    def get_mapping(self, source_name: str) -> Dict:
        """Get mapping for a source"""
        return self.mappings.get(source_name, {})

    def apply_mapping(self, df: pd.DataFrame, mapping: Dict) -> pd.DataFrame:
        """Apply column mapping to dataframe"""
        text_columns = mapping.get("text_columns", [])
        comment_columns = mapping.get("comment_columns", [])
        id_column = mapping.get("id_column")

        # Extract relevant columns
        columns_to_keep = text_columns.copy()
        columns_to_keep.extend(comment_columns)

        if id_column and id_column not in columns_to_keep:
            columns_to_keep.insert(0, id_column)

        # Add metadata columns if they exist
        for metadata_col in ['Parent', 'Issue Type', 'Issue type']:
            if metadata_col in df.columns and metadata_col not in columns_to_keep:
                columns_to_keep.append(metadata_col)

        # Filter to existing columns only
        columns_to_keep = [col for col in columns_to_keep if col in df.columns]

        # Filter dataframe
        df_filtered = df[columns_to_keep] if columns_to_keep else df

        return df_filtered
