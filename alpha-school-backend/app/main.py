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

# Disable CORS. Do not remove this for full-stack development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
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
