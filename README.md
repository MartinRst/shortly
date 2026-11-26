# Shortly

A small link shortener built with FastAPI and SQLite.

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --port 8000
python3 tests/smoke_test.py http://127.0.0.1:8000
```
