# alpha-school backend

FastAPI + SQLite backend for ThriveEd.

## Setup

```bash
poetry install
cp .env.example .env
# Edit .env: at minimum, set JWT_SECRET_KEY.
# Generate one with:
python -c 'import secrets; print(secrets.token_urlsafe(64))'
```

## Run (development)

The server reads configuration from environment variables. Use `uvicorn`'s
`--env-file` flag so it picks up your local `.env`:

```bash
poetry run uvicorn app.main:app --reload --env-file .env
```

Or export the variables in your shell before starting:

```bash
export $(grep -v '^#' .env | xargs)
poetry run fastapi dev app/main.py
```

## Required environment variables

| Variable                | Required | Default                  | Notes                                      |
| ----------------------- | -------- | ------------------------ | ------------------------------------------ |
| `JWT_SECRET_KEY`        | yes      | —                        | App refuses to start without this          |
| `JWT_EXPIRE_HOURS`      | no       | `24`                     | Token lifetime                             |
| `CORS_ALLOWED_ORIGINS`  | no       | `http://localhost:5173`  | Comma-separated; no wildcards              |

## Database

SQLite, auto-initialized on startup. The `seed.py` module populates demo data
on every boot — disable or guard this before deploying to production.
