import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db
from app.seed import seed_database
from app.routes.auth_routes import router as auth_router
from app.routes.admin_routes import router as admin_router
from app.routes.student_routes import router as student_router
from app.routes.coach_routes import router as coach_router
from app.routes.parent_routes import router as parent_router

app = FastAPI(title="ThriveEd", version="1.0.0")

_cors_origins = os.environ.get("CORS_ALLOWED_ORIGINS", "http://localhost:5173")
allowed_origins = [o.strip() for o in _cors_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

# Include routers
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(student_router)
app.include_router(coach_router)
app.include_router(parent_router)

@app.on_event("startup")
def startup():
    init_db()
    seed_database()

@app.get("/healthz")
async def healthz():
    return {"status": "ok"}
