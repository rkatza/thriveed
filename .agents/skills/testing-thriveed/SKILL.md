# Testing ThriveEd App

## Local Development Setup

### Backend
```bash
cd alpha-school-backend
poetry install
poetry run uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd alpha-school-frontend
# Create .env.local with VITE_API_URL=http://localhost:8000
npm install
npm run dev -- --host 0.0.0.0 --port 5173
```

### Production (Railway)
- Frontend: https://frontend-production-1866.up.railway.app
- Backend: https://backend-production-e8be.up.railway.app
- Auto-deploys on merge to `initial-setup` branch

## Test Accounts

| Role | Email | Password | Notes |
|------|-------|----------|-------|
| Admin | admin@thriveed.edu.pa | admin123 | Super admin, all permissions |
| Coach | coach1@thriveed.edu.pa | coach123 | Coach María |
| Student (4to) | sofia@thriveed.edu.pa | student123 | Sofia Martinez, placement done |
| Student (Kinder) | mateo@thriveed.edu.pa | student123 | Mateo Garcia, placement NOT done |
| Parent | padre.martinez@gmail.com | parent123 | Roberto Martinez |

## Key Database Facts
- Kinder classroom_id: 3 (grade_id=2, level=0)
- 4to Grado classroom_ids: 1, 2 (grade_id=1, level=4)
- `curriculum_level` is derived from classroom grade, not stored on student directly
- Students without a classroom default to `4to_grado`

## Mobile Testing

### Viewport Sizes
- Mobile: 375px width (hamburger menu visible, sidebar hidden)
- Tablet: 768px width (breakpoint where `md:` classes activate)
- Desktop: 1024px+ (sidebar always visible)

### Resizing Browser
```bash
# Remove maximize first, then resize
wmctrl -r "Google Chrome" -b remove,maximized_vert,maximized_horz
sleep 0.5
wmctrl -r "Google Chrome" -e 0,0,0,375,768  # mobile

# Back to desktop
wmctrl -r "Google Chrome" -b add,maximized_vert,maximized_horz
```

### Sidebar Behavior
- Mobile (<768px): Hidden by default, hamburger opens, overlay/X/Escape/route-change closes
- Desktop (>=768px): Always visible, no hamburger, content has `md:ml-64` margin

## TTS (Text-to-Speech) Testing

### Known Limitation
Headless Chrome environments (like Devin's VM) have **0 voices** loaded in `speechSynthesis.getVoices()`. The `SpeechSynthesis` API is available but cannot produce audio without voices. This means:
- The "Escuchar" button renders and is clickable
- `speechSynthesis.speak()` is called without errors
- But no actual audio is produced
- `voicesReady` state never becomes true, so auto-speak doesn't trigger

### What CAN Be Verified in Headless
- Button visibility (only for `curriculum_level === 'kinder'`)
- Button click triggers speak() call
- Button state management (speaking/not speaking via React state)
- SpeechSynthesis API availability

### What REQUIRES Real Device
- Actual audio output in Spanish (es-MX)
- Auto-speak on question change
- Voice selection (Spanish voice preference)
- Rate (0.85) and pitch (1.1) parameters

### Programmatic Verification via Playwright
```python
import asyncio
from playwright.async_api import async_playwright

async def check_tts():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://localhost:29229")
        page = browser.contexts[0].pages[0]
        btn = await page.query_selector('button[aria-label="Leer en voz alta"]')
        if btn:
            text = await btn.inner_text()
            print(f"TTS Button found: '{text}'")  # Should be 'Escuchar'
        await browser.close()

asyncio.run(check_tts())
```

## Admin Create Student Testing
- Navigate to Admin > Estudiantes
- Click "Crear Estudiante" button
- Fill form: Nombre, Apellido, Email, Contraseña, Edad, Nivel (Kinder/4to Grado)
- Nivel dropdown defaults to "Kinder (5-6 años)"
- Backend auto-assigns classroom based on curriculum_level
- If no matching classroom exists, backend returns 400 with descriptive error

## Chrome Setup on Devin VM
Chrome must be started with CDP for the `google-chrome` wrapper to work:
```bash
/opt/.devin/chrome/chrome/linux-133.0.6943.126/chrome-linux64/chrome \
  --remote-debugging-port=29229 \
  --no-first-run \
  --disable-session-crashed-bubble \
  --disable-infobars \
  --no-default-browser-check \
  --user-data-dir=/tmp/chrome-test \
  http://localhost:5173/login 2>/dev/null &
```

Then use `wmctrl -a "Google Chrome"` to bring to foreground and `wmctrl -r "Google Chrome" -b add,maximized_vert,maximized_horz` to maximize.

## Devin Secrets Needed
- `RAILWAY_TOKEN` — Railway API token for deployment operations
