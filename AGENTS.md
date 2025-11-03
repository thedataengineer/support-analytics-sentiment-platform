# Repository Guidelines

## Project Structure & Module Organization
- `backend/` runs the FastAPI service: request handlers in `api/`, business logic in `services/`, persistence in `models/`, and Celery jobs in `jobs/`.
- `client/` houses the React UI (Material UI, Chart.js) under `client/src`; share reusable pieces in `client/src/components`.
- `ml/` provides the standalone NLP workers (`app.py`, `sentiment_model/`, `ner_model/`), while `db/` stores SQL bootstrap scripts and root `test_*.py` files exercise cross-service flows.

## Build, Test, and Development Commands
- Provision infrastructure services with `docker-compose up -d` from the repository root.
- Start the API via `cd backend && source venv/bin/activate && uvicorn main:app --reload`; launch the ML worker with `cd ml && source venv/bin/activate && python app.py`.
- Serve the frontend with `cd client && npm install && npm start`, build releases via `npm run build`, and run core suites using `cd backend && pytest`, `cd client && npm test`, and `cd ml && python -m pytest`.

## Coding Style & Naming Conventions
- Target Python 3.11, follow PEP 8, keep modules, services, and tasks in snake_case, and add type hints on new code paths.
- React files align with `react-scripts` ESLint and Prettier; keep components PascalCase and utilities camelCase.
- Reference `.env.example` when adding configuration; never commit secrets to `config.py`, checked-in notebooks, or `client/src`.

## Testing Guidelines
- Place fast unit tests alongside modules or under `backend/tests/`, and reuse the integration harness already in `test_end_to_end.py` and `test_jira_ingest.py`.
- Name Python tests `test_<feature>.py`; flag slow or external-resource scenarios with `@pytest.mark.integration` for selective runs.
- Frontend specs live in `client/src/__tests__/` with Jest + React Testing Library; record sample CSV usage (for example `sample_data.csv`) in docs or PR notes.

## Commit & Pull Request Guidelines
- Existing history favors concise, imperative commit subjects with optional scope (e.g., `feat(api): add bulk ingestion`); keep commits scoped per area (backend, client, ml).
- Before opening a PR, rebase or squash noisy iterations and describe user impact plus verification commands; link Jira issues or GitHub tickets when available.
- Capture new environment variables, migrations, or UI changes in the PR description, attach screenshots for visual tweaks, and request reviewers from each affected surface.

## Security & Configuration Tips
- Load secrets through environment variables or secret stores; avoid embedding tokens or credentials in source-controlled files.
- Clean `uploads/` and reset local service volumes with `docker-compose down -v` before sharing logs or artifacts outside the team.
