# FastAPI + Supabase Backend

## Setup
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Tests
```bash
pytest tests/ --cov=app --cov-report=term-missing
```

## Alembic
```bash
alembic revision --autogenerate -m "initial"
alembic upgrade head
```
