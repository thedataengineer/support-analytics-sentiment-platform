import requests
import json
from typing import Dict, List, Optional
import os
from dotenv import load_dotenv

load_dotenv()

ML_SERVICE_URL = os.getenv("ML_SERVICE_URL", "http://localhost:5001")

class NLPClient:
    def __init__(self, base_url: str = ML_SERVICE_URL):
        self.base_url = base_url

    def get_sentiment(self, text: str) -> Dict:
        """
        Get sentiment analysis for text
        """
        try:
            response = requests.post(
                f"{self.base_url}/ml/analyze-sentiment",
                json={"text": text},
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            # Fallback for MVP - return neutral sentiment
            print(f"ML service error: {e}")
            return {"sentiment": "neutral", "confidence": 0.5}

    def get_entities(self, text: str) -> List[Dict]:
        """
        Extract named entities from text
        """
        try:
            response = requests.post(
                f"{self.base_url}/ml/extract-entities",
                json={"text": text},
                timeout=10
            )
            response.raise_for_status()
            return response.json().get("entities", [])
        except requests.RequestException as e:
            # Fallback for MVP - return empty list
            print(f"ML service error: {e}")
            return []

# Global client instance
nlp_client = NLPClient()
