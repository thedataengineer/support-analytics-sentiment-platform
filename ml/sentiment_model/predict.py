from transformers import pipeline
import torch

class SentimentAnalyzer:
    def __init__(self):
        # Load pre-trained sentiment analysis model
        self.model = pipeline(
            "sentiment-analysis",
            model="distilbert-base-uncased-finetuned-sst-2-english",
            device=0 if torch.cuda.is_available() else -1
        )

    def predict(self, text: str) -> dict:
        """
        Predict sentiment for given text
        """
        if not text or not text.strip():
            return {"sentiment": "neutral", "confidence": 0.5}

        try:
            result = self.model(text)[0]

            # Map model output to our format
            label = result['label'].lower()
            if label == 'positive':
                sentiment = 'positive'
            elif label == 'negative':
                sentiment = 'negative'
            else:
                sentiment = 'neutral'

            return {
                "sentiment": sentiment,
                "confidence": round(result['score'], 3)
            }
        except Exception as e:
            print(f"Error in sentiment prediction: {e}")
            return {"sentiment": "neutral", "confidence": 0.5}

# Global instance
sentiment_analyzer = SentimentAnalyzer()
