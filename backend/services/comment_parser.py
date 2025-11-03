"""
Comment Parser for Jira comments with embedded temporal metadata
"""
import re
from datetime import datetime
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)


class CommentParser:
    """Parse Jira comments in format: 'DD/MMM/YY HH:MM AM/PM;author_id;comment_text'"""

    # Pattern: 10/Oct/25 11:45 AM;5f05c9e30b38b1002265;Message text...
    COMMENT_PATTERN = re.compile(
        r'^(\d{2}/\w{3}/\d{2}\s+\d{1,2}:\d{2}\s+[AP]M);([^;]+);(.+)',
        re.DOTALL
    )

    @classmethod
    def parse(cls, comment_text: str) -> Dict:
        """
        Parse a comment string and extract metadata

        Returns:
            dict with keys: timestamp, author_id, text, is_parsed
        """
        if not comment_text or not isinstance(comment_text, str):
            return {
                'timestamp': None,
                'author_id': None,
                'text': comment_text or '',
                'is_parsed': False
            }

        comment_text = comment_text.strip()
        if not comment_text:
            return {
                'timestamp': None,
                'author_id': None,
                'text': '',
                'is_parsed': False
            }

        match = cls.COMMENT_PATTERN.match(comment_text)
        if match:
            timestamp_str = match.group(1)
            author_id = match.group(2).strip()
            text = match.group(3).strip()

            # Parse timestamp
            timestamp = cls._parse_timestamp(timestamp_str)

            return {
                'timestamp': timestamp,
                'author_id': author_id,
                'text': text,
                'is_parsed': True
            }
        else:
            # Comment doesn't match expected format
            # Treat entire text as comment content
            return {
                'timestamp': None,
                'author_id': None,
                'text': comment_text,
                'is_parsed': False
            }

    @classmethod
    def _parse_timestamp(cls, timestamp_str: str) -> Optional[datetime]:
        """
        Parse timestamp string to datetime
        Format: '10/Oct/25 11:45 AM'
        """
        try:
            # Parse format: DD/MMM/YY HH:MM AM/PM
            dt = datetime.strptime(timestamp_str, '%d/%b/%y %I:%M %p')
            return dt
        except Exception as e:
            logger.warning(f"Failed to parse timestamp '{timestamp_str}': {e}")
            return None
