FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    PYTHONPATH=/app

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends build-essential curl && rm -rf /var/lib/apt/lists/*

COPY ml/requirements.txt ml/requirements.txt

RUN pip install --upgrade pip && pip install -r ml/requirements.txt

# Download spacy model
RUN python -m spacy download en_core_web_sm

COPY ml /app/ml

EXPOSE 5001

CMD ["python", "ml/app.py"]
