# Sentiment Analysis Platform MVP

A production-ready MVP for text sentiment analysis platform that ingests Jira Service Desk CSV exports and provides dashboards and reports.

## Features

- **CSV Upload**: Upload and process large CSV files (up to 500MB, 10k rows × 1,670 columns)
- **Sentiment Analysis**: Real-time sentiment classification using HuggingFace Transformers
- **Named Entity Recognition**: Extract entities like products, brands, and organizations using spaCy
- **Dashboard**: Interactive charts showing sentiment trends and distributions
- **PDF Reports**: Generate comprehensive sentiment analysis reports
- **Search**: Full-text search capabilities with Elasticsearch
- **Authentication**: JWT-based user authentication with role-based access control

## Tech Stack

- **Frontend**: React.js, Material-UI, Chart.js
- **Backend**: Python 3.11+, FastAPI, Celery, SQLAlchemy
- **ML/NLP**: spaCy, HuggingFace Transformers
- **Database**: PostgreSQL, Elasticsearch
- **DevOps**: Docker, docker-compose

## Quick Start

### Prerequisites

- Docker and docker-compose
- Node.js 16+ and npm
- Python 3.11+

### 1. Clone and Setup Infrastructure

```bash
git clone <repo-url>
cd sentiment-platform

# Start infrastructure services
docker-compose up -d
```

### 2. Setup Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Initialize database
psql -h localhost -U sentiment_user -d sentiment_db -f ../db/init.sql

# Start backend server
uvicorn main:app --reload
```

### 3. Setup ML Service

```bash
cd ../ml
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm

# Start ML service
python app.py
```

### 4. Setup Frontend

```bash
cd ../client
npm install
npm start
```

### 5. Start Celery Worker (Optional for async processing)

```bash
cd ../backend
celery -A jobs.celery_config worker --loglevel=info
```

## API Documentation

Once the backend is running, visit `http://localhost:8000/docs` for interactive API documentation.

## Usage

1. **Login**: Use demo credentials `admin@example.com` / `password`
2. **Upload CSV**: Go to Upload page and drag/drop a CSV file
3. **View Dashboard**: Check sentiment trends and distributions
4. **Generate Reports**: Download PDF reports with charts and insights
5. **Search**: Use search functionality to find specific tickets

## Development

### Project Structure

```
sentiment-platform/
├── client/                 # React frontend
├── backend/               # FastAPI backend
│   ├── api/              # API endpoints
│   ├── models/           # SQLAlchemy models
│   ├── services/         # Business logic
│   └── jobs/             # Celery tasks
├── ml/                   # ML services
│   ├── sentiment_model/  # Sentiment analysis
│   └── ner_model/        # Named entity recognition
├── db/                   # Database setup
└── docker-compose.yml    # Infrastructure
```

### Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd client
npm test

# ML service tests
cd ml
python -m pytest
```

### Code Quality

- **Python**: Follow PEP 8, use type hints, add docstrings
- **JavaScript**: Use ESLint and Prettier
- **Git**: Feature branch workflow with descriptive commits

## Deployment

### Production Setup

1. Update environment variables in `.env` files
2. Use managed **PostgreSQL** and Elasticsearch
3. Deploy backend to AWS ECS/GKE
4. Deploy frontend to S3 + CloudFront
5. Set up CI/CD with GitHub Actions

### Environment Variables

Create `.env` files in backend/ and ml/ directories:

```bash
# backend/.env
DATABASE_URL=postgresql://user:pass@host:5432/db
SECRET_KEY=your-secret-key
REDIS_URL=redis://localhost:6379

# ml/.env
MODEL_CACHE_DIR=/path/to/cache
```

## Performance Benchmarks

- Dashboard loads in < 2 seconds
- CSV upload (10k rows) processes in < 5 minutes
- Sentiment accuracy > 85%
- Handles 100k+ tickets without degradation

## Contributing

1. Create feature branch from `main`
2. Write tests for new functionality
3. Ensure code passes linting
4. Submit pull request with description

## License

MIT License - see LICENSE file for details.
