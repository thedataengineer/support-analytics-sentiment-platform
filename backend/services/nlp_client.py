from __future__ import annotations

import logging
from typing import Any, Dict, List

import requests

from config import settings

logger = logging.getLogger(__name__)


class NLPClient:
    """
    Client for the local ML microservice that provides sentiment and entity analysis.
    """

    def __init__(self):
        self.base_url = settings.ml_service_url.rstrip("/")

    def _post(self, path: str, payload: Dict[str, str]) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        return response.json()

    def get_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Fetch sentiment analysis for the provided text.
        """
        if not text or not text.strip():
            return {"sentiment": "neutral", "confidence": 0.5}

        truncated = text[:5000].strip()
        try:
            data = self._post("/ml/analyze-sentiment", {"text": truncated})
            return {
                "sentiment": data.get("sentiment", "neutral"),
                "confidence": data.get("confidence", 0.5),
            }
        except Exception as exc:
            logger.warning("ML sentiment analysis failed: %s", exc)
            return {"sentiment": "neutral", "confidence": 0.5}

    def get_entities(self, text: str) -> List[Dict[str, Any]]:
        """
        Fetch named entity recognition results for the provided text.
        """
        if not text or not text.strip():
            return []

        truncated = text[:5000]
        try:
            data = self._post("/ml/extract-entities", {"text": truncated})
            return data.get("entities", [])
        except Exception as exc:
            logger.warning("ML entity extraction failed: %s", exc)
            return []


# Global client instance
nlp_client = NLPClient()
