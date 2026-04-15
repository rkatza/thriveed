# ThriveEd Testing Skills

## Local Development

```bash
# Backend (FastAPI + SQLite)
cd alpha-school-backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# Frontend (Vite + React)
cd alpha-school-frontend && npm run dev
# Frontend runs on http://localhost:5173
```

The backend seeds a fresh SQLite database on startup with demo data.

## Demo Accounts

See `alpha-school-backend/app/seed.py` for all demo accounts and passwords.
The login page has demo account buttons for quick access — no need to type credentials.

Key accounts:
- **Admin**: admin@thriveed.edu.pa
- **Coach**: maria@thriveed.edu.pa
- **Student (4to Grado)**: sofia@thriveed.edu.pa (placement_test_completed=true, goes to dashboard)
- **Student (Kinder)**: mateo@thriveed.edu.pa (placement_test_completed=false, sees visual mode)
- **Parent**: padre.martinez@gmail.com

## Kinder Visual Mode Testing

Kinder students (grade level 0) get emoji-based visual questions with TTS audio.

**Key checks:**
- Login as Mateo -> redirects to placement test (not dashboard)
- Questions show large emoji images (not text)
- Options are emoji buttons in 2-column grid (not text strings)
- "Escuchar" button visible for TTS replay
- After confirming answer: correct option gets green highlight + checkmark
- Auto-advances to next question after ~1.5s
- `curriculum_level` must be lowercase `'kinder'` (auth endpoints normalize from grades.level)

**Regression check:**
- Login as Sofia (4to grado) -> goes to dashboard
- Questions show as text with text input/text option buttons
- No emoji cards, no "Escuchar" button

## Curriculum Level Detection

The system normalizes curriculum level from `grades.level` column:
- level=0 -> `'kinder'`
- level!=0 -> `'4to_grado'`

This normalization happens in:
- `auth_routes.py` (/login and /me endpoints)
- `student_routes.py` (get_student_curriculum_level)

**Important:** The `grades.name` column has capitalized values ('Kinder', '4to Grado') but the system uses lowercase normalized keys ('kinder', '4to_grado'). Always use `grades.level` for detection, never `grades.name`.

## Flow Engine Grade-Specific Config

Kinder uses different Flow Engine parameters (KINDER_CFG):
- Wider flow band: P_MIN=0.75, P_MAX=0.88 (vs default 0.70-0.80)
- Lower K_STUDENT=20 (vs default 32) -- slower theta movement
- Faster rescue: after 1 wrong (vs default 2)
- Grade config resolved via `config_for_grade(curriculum_level)` and passed to all Flow Engine functions

## Railway Deployment

- Frontend: https://frontend-production-1866.up.railway.app
- Backend: https://backend-production-e8be.up.railway.app
- Auto-deploys from `initial-setup` branch
- Backend uses persistent SQLite volume at /data/app.db

## Build & Lint

```bash
# Frontend lint
cd alpha-school-frontend && npm run lint

# Frontend build
cd alpha-school-frontend && npm run build

# Backend tests (Flow Engine)
cd alpha-school-backend && python -m pytest tests/test_flow_engine.py -v
```
