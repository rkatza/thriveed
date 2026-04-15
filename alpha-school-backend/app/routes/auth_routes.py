from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.database import get_db
from app.auth import hash_password, verify_password, create_access_token, get_current_user
from fastapi import Depends

router = APIRouter(prefix="/api/auth", tags=["auth"])

class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    email: str
    password: str
    role: str
    first_name: str
    last_name: str

@router.post("/login")
async def login(req: LoginRequest):
    with get_db() as db:
        user = db.execute("SELECT * FROM users WHERE email = ?", (req.email,)).fetchone()
        if not user or not verify_password(req.password, user["password_hash"]):
            raise HTTPException(status_code=401, detail="Email o contraseña incorrectos")
        if not user["is_active"]:
            raise HTTPException(status_code=403, detail="Cuenta desactivada")
        
        token = create_access_token({
            "user_id": user["id"],
            "email": user["email"],
            "role": user["role"]
        })
        
        # Get role-specific info
        extra = {}
        if user["role"] == "student":
            student = db.execute("SELECT * FROM students WHERE user_id = ?", (user["id"],)).fetchone()
            if student:
                # Resolve curriculum_level from classroom -> grade
                curriculum_level = None
                if student["classroom_id"]:
                    cls_row = db.execute(
                        "SELECT g.level FROM classrooms c JOIN grades g ON c.grade_id = g.id WHERE c.id = ?",
                        (student["classroom_id"],),
                    ).fetchone()
                    if cls_row:
                        curriculum_level = "kinder" if cls_row["level"] == 0 else "4to_grado"
                extra = {"student_id": student["id"], "nickname": student["nickname"], "avatar_url": student["avatar_url"],
                         "placement_test_completed": bool(student["placement_test_completed"]),
                         "curriculum_level": curriculum_level}
        elif user["role"] == "coach":
            coach = db.execute("SELECT * FROM coaches WHERE user_id = ?", (user["id"],)).fetchone()
            if coach:
                extra = {"coach_id": coach["id"], "classroom_id": coach["classroom_id"]}
        elif user["role"] == "parent":
            parent = db.execute("SELECT * FROM parents WHERE user_id = ?", (user["id"],)).fetchone()
            if parent:
                extra = {"parent_id": parent["id"]}
        
        return {
            "token": token,
            "user": {
                "id": user["id"],
                "email": user["email"],
                "role": user["role"],
                "first_name": user["first_name"],
                "last_name": user["last_name"],
                **extra
            }
        }

@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    with get_db() as db:
        user = db.execute("SELECT * FROM users WHERE id = ?", (current_user["user_id"],)).fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        extra = {}
        if user["role"] == "student":
            student = db.execute("SELECT * FROM students WHERE user_id = ?", (user["id"],)).fetchone()
            if student:
                curriculum_level = None
                if student["classroom_id"]:
                    cls_row = db.execute(
                        "SELECT g.level FROM classrooms c JOIN grades g ON c.grade_id = g.id WHERE c.id = ?",
                        (student["classroom_id"],),
                    ).fetchone()
                    if cls_row:
                        curriculum_level = "kinder" if cls_row["level"] == 0 else "4to_grado"
                extra = {"student_id": student["id"], "nickname": student["nickname"], "avatar_url": student["avatar_url"],
                         "placement_test_completed": bool(student["placement_test_completed"]),
                         "interests": student["interests"], "age": student["age"],
                         "curriculum_level": curriculum_level}
        elif user["role"] == "coach":
            coach = db.execute("SELECT * FROM coaches WHERE user_id = ?", (user["id"],)).fetchone()
            if coach:
                extra = {"coach_id": coach["id"], "classroom_id": coach["classroom_id"]}
        elif user["role"] == "parent":
            parent = db.execute("SELECT * FROM parents WHERE user_id = ?", (user["id"],)).fetchone()
            if parent:
                extra = {"parent_id": parent["id"]}
        
        return {
            "id": user["id"],
            "email": user["email"],
            "role": user["role"],
            "first_name": user["first_name"],
            "last_name": user["last_name"],
            **extra
        }

@router.post("/register")
async def register(req: RegisterRequest):
    with get_db() as db:
        existing = db.execute("SELECT id FROM users WHERE email = ?", (req.email,)).fetchone()
        if existing:
            raise HTTPException(status_code=400, detail="El email ya está registrado")
        
        db.execute("INSERT INTO users (email, password_hash, role, first_name, last_name) VALUES (?, ?, ?, ?, ?)",
                   (req.email, hash_password(req.password), req.role, req.first_name, req.last_name))
        user_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
        
        if req.role == "student":
            db.execute("INSERT INTO students (user_id, nickname) VALUES (?, ?)", (user_id, req.first_name))
        elif req.role == "coach":
            db.execute("INSERT INTO coaches (user_id) VALUES (?)", (user_id,))
        elif req.role == "parent":
            db.execute("INSERT INTO parents (user_id) VALUES (?)", (user_id,))
        
        token = create_access_token({"user_id": user_id, "email": req.email, "role": req.role})
        return {"token": token, "user": {"id": user_id, "email": req.email, "role": req.role,
                                          "first_name": req.first_name, "last_name": req.last_name}}
