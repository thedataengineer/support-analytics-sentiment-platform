import spacy
from typing import List, Dict

class EntityExtractor:
    def __init__(self):
        # Load spaCy model
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            # If model not found, download it
            spacy.cli.download("en_core_web_sm")
            self.nlp = spacy.load("en_core_web_sm")

    def extract(self, text: str) -> List[Dict]:
        """
        Extract named entities from text
        """
        if not text or not text.strip():
            return []

        try:
            doc = self.nlp(text)

            entities = []
            for ent in doc.ents:
                # Map spaCy labels to our format
                label = self._map_label(ent.label_)

                entity = {
                    "text": ent.text,
                    "label": label,
                    "start": ent.start_char,
                    "end": ent.end_char
                }
                entities.append(entity)

            return entities
        except Exception as e:
            print(f"Error in entity extraction: {e}")
            return []

    def _map_label(self, spacy_label: str) -> str:
        """
        Map spaCy entity labels to our custom labels
        """
        label_mapping = {
            'PERSON': 'PERSON',
            'ORG': 'ORGANIZATION',
            'GPE': 'LOCATION',
            'LOC': 'LOCATION',
            'MONEY': 'MONEY',
            'DATE': 'DATE',
            'TIME': 'TIME',
            'PERCENT': 'PERCENT',
            'PRODUCT': 'PRODUCT',
            'EVENT': 'EVENT',
            'WORK_OF_ART': 'WORK_OF_ART',
            'LAW': 'LAW',
            'LANGUAGE': 'LANGUAGE'
        }

        # If it's a product-related term, classify as PRODUCT
        if spacy_label not in label_mapping:
            return 'MISC'

        return label_mapping[spacy_label]

# Global instance
entity_extractor = EntityExtractor()
