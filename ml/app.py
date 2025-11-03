from flask import Flask, request, jsonify
from flask_cors import CORS
from sentiment_model.predict import sentiment_analyzer
from ner_model.extract import entity_extractor

app = Flask(__name__)
CORS(app)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy"})

@app.route('/ml/analyze-sentiment', methods=['POST'])
def analyze_sentiment():
    """
    Analyze sentiment of provided text
    """
    try:
        data = request.get_json()
        text = data.get('text', '')

        if not text:
            return jsonify({"error": "No text provided"}), 400

        result = sentiment_analyzer.predict(text)
        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/ml/extract-entities', methods=['POST'])
def extract_entities():
    """
    Extract named entities from provided text
    """
    try:
        data = request.get_json()
        text = data.get('text', '')

        if not text:
            return jsonify({"entities": []})

        entities = entity_extractor.extract(text)
        return jsonify({"entities": entities})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
