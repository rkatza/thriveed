from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from app.database import get_db
from app.auth import get_current_user, require_roles, hash_password
import json, csv, io, uuid
from datetime import datetime, timedelta
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/api/admin", tags=["admin"])

# ---- Models ----
class SchoolCreate(BaseModel):
    name: str
    address: Optional[str] = None
    city: Optional[str] = "Ciudad de Panamá"
    phone: Optional[str] = None

class GradeCreate(BaseModel):
    school_id: int
    name: str
    level: int = 4

class ClassroomCreate(BaseModel):
    grade_id: int
    name: str
    group_type: str = "treatment"

class StudentCreate(BaseModel):
    email: str
    password: str
    first_name: str
    last_name: str
    classroom_id: Optional[int] = None
    age: int = 9
    interests: str = "[]"
    curriculum_level: Optional[str] = None

class CoachCreate(BaseModel):
    email: str
    password: str
    first_name: str
    last_name: str
    classroom_id: Optional[int] = None
    specialization: Optional[str] = None

class ParentCreate(BaseModel):
    email: str
    password: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    student_ids: list[int] = []

class InvitationCreate(BaseModel):
    email: str
    role: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    curriculum_level: Optional[str] = "4to_grado"
    classroom_id: Optional[int] = None

# ---- Dashboard ----
@router.get("/dashboard")
async def dashboard(current_user: dict = Depends(require_roles("super_admin", "admin"))):
    with get_db() as db:
        total_students = db.execute("SELECT COUNT(*) as c FROM students").fetchone()["c"]
        active_sessions = db.execute("SELECT COUNT(*) as c FROM daily_sessions WHERE session_date = date('now')").fetchone()["c"]
        completed_sessions = db.execute("SELECT COUNT(*) as c FROM daily_sessions WHERE session_date = date('now') AND status = 'completed'").fetchone()["c"]
        avg_time = db.execute("SELECT COALESCE(AVG(active_time_seconds), 0) as avg FROM daily_sessions WHERE status = 'completed'").fetchone()["avg"]
        avg_mastery = db.execute("SELECT COALESCE(AVG(mastery_level), 0) as avg FROM mastery_signals").fetchone()["avg"]
        alerts = db.execute("SELECT COUNT(*) as c FROM help_requests WHERE status = 'pending'").fetchone()["c"]
        total_coaches = db.execute("SELECT COUNT(*) as c FROM coaches").fetchone()["c"]
        total_parents = db.execute("SELECT COUNT(*) as c FROM parents").fetchone()["c"]
        placement_done = db.execute("SELECT COUNT(*) as c FROM students WHERE placement_test_completed = 1").fetchone()["c"]
        
        # Recent sessions
        recent_sessions = db.execute("""
            SELECT ds.*, u.first_name, u.last_name, s.name as skill_name
            FROM daily_sessions ds
            JOIN students st ON ds.student_id = st.id
            JOIN users u ON st.user_id = u.id
            LEFT JOIN skills s ON ds.target_skill_id = s.id
            ORDER BY ds.started_at DESC LIMIT 10
        """).fetchall()
        
        return {
            "total_students": total_students,
            "active_sessions_today": active_sessions,
            "completed_sessions_today": completed_sessions,
            "avg_session_time_minutes": round(avg_time / 60, 1),
            "avg_mastery_rate": round(avg_mastery * 100, 1),
            "pending_alerts": alerts,
            "total_coaches": total_coaches,
            "total_parents": total_parents,
            "placement_tests_completed": placement_done,
            "recent_sessions": [dict(s) for s in recent_sessions]
        }

# ---- Schools CRUD ----
@router.get("/schools")
async def list_schools(current_user: dict = Depends(require_roles("super_admin", "admin"))):
    with get_db() as db:
        schools = db.execute("SELECT * FROM schools ORDER BY created_at DESC").fetchall()
        return [dict(s) for s in schools]

@router.post("/schools")
async def create_school(school: SchoolCreate, current_user: dict = Depends(require_roles("super_admin", "admin"))):
    with get_db() as db:
        db.execute("INSERT INTO schools (name, address, city, phone) VALUES (?, ?, ?, ?)",
                   (school.name, school.address, school.city, school.phone))
        sid = db.execute("SELECT last_insert_rowid()").fetchone()[0]
        db.execute("INSERT INTO audit_log (user_id, action, entity_type, entity_id, details) VALUES (?, ?, ?, ?, ?)",
                   (current_user["user_id"], "create", "school", sid, school.name))
        return {"id": sid, "message": "Escuela creada"}

@router.put("/schools/{school_id}")
async def update_school(school_id: int, school: SchoolCreate, current_user: dict = Depends(require_roles("super_admin", "admin"))):
    with get_db() as db:
        db.execute("UPDATE schools SET name=?, address=?, city=?, phone=? WHERE id=?",
                   (school.name, school.address, school.city, school.phone, school_id))
        db.execute("INSERT INTO audit_log (user_id, action, entity_type, entity_id, details) VALUES (?, ?, ?, ?, ?)",
                   (current_user["user_id"], "update", "school", school_id, school.name))
        return {"message": "Escuela actualizada"}

@router.delete("/schools/{school_id}")
async def delete_school(school_id: int, current_user: dict = Depends(require_roles("super_admin"))):
    with get_db() as db:
        db.execute("DELETE FROM schools WHERE id=?", (school_id,))
        db.execute("INSERT INTO audit_log (user_id, action, entity_type, entity_id) VALUES (?, ?, ?, ?)",
                   (current_user["user_id"], "delete", "school", school_id))
        return {"message": "Escuela eliminada"}

# ---- Grades CRUD ----
@router.get("/grades")
async def list_grades(school_id: Optional[int] = None, current_user: dict = Depends(require_roles("super_admin", "admin"))):
    with get_db() as db:
        if school_id:
            grades = db.execute("SELECT g.*, s.name as school_name FROM grades g JOIN schools s ON g.school_id = s.id WHERE g.school_id = ?", (school_id,)).fetchall()
        else:
            grades = db.execute("SELECT g.*, s.name as school_name FROM grades g JOIN schools s ON g.school_id = s.id ORDER BY g.created_at DESC").fetchall()
        return [dict(g) for g in grades]

@router.post("/grades")
async def create_grade(grade: GradeCreate, current_user: dict = Depends(require_roles("super_admin", "admin"))):
    with get_db() as db:
        db.execute("INSERT INTO grades (school_id, name, level) VALUES (?, ?, ?)",
                   (grade.school_id, grade.name, grade.level))
        gid = db.execute("SELECT last_insert_rowid()").fetchone()[0]
        db.execute("INSERT INTO audit_log (user_id, action, entity_type, entity_id, details) VALUES (?, ?, ?, ?, ?)",
                   (current_user["user_id"], "create", "grade", gid, grade.name))
        return {"id": gid, "message": "Grado creado"}

# ---- Classrooms CRUD ----
@router.get("/classrooms")
async def list_classrooms(grade_id: Optional[int] = None, current_user: dict = Depends(require_roles("super_admin", "admin"))):
    with get_db() as db:
        if grade_id:
            classrooms = db.execute("""SELECT c.*, g.name as grade_name, s.name as school_name 
                                       FROM classrooms c JOIN grades g ON c.grade_id = g.id JOIN schools s ON g.school_id = s.id
                                       WHERE c.grade_id = ?""", (grade_id,)).fetchall()
        else:
            classrooms = db.execute("""SELECT c.*, g.name as grade_name, s.name as school_name 
                                       FROM classrooms c JOIN grades g ON c.grade_id = g.id JOIN schools s ON g.school_id = s.id
                                       ORDER BY c.created_at DESC""").fetchall()
        return [dict(c) for c in classrooms]

@router.post("/classrooms")
async def create_classroom(classroom: ClassroomCreate, current_user: dict = Depends(require_roles("super_admin", "admin"))):
    with get_db() as db:
        db.execute("INSERT INTO classrooms (grade_id, name, group_type) VALUES (?, ?, ?)",
                   (classroom.grade_id, classroom.name, classroom.group_type))
        cid = db.execute("SELECT last_insert_rowid()").fetchone()[0]
        db.execute("INSERT INTO audit_log (user_id, action, entity_type, entity_id, details) VALUES (?, ?, ?, ?, ?)",
                   (current_user["user_id"], "create", "classroom", cid, classroom.name))
        return {"id": cid, "message": "Salón creado"}

# ---- Students CRUD ----
@router.get("/students")
async def list_students(classroom_id: Optional[int] = None, current_user: dict = Depends(require_roles("super_admin", "admin"))):
    with get_db() as db:
        query = """SELECT s.*, u.email, u.first_name, u.last_name, u.is_active,
                          c.name as classroom_name, g.name as grade_name
                   FROM students s
                   JOIN users u ON s.user_id = u.id
                   LEFT JOIN classrooms c ON s.classroom_id = c.id
                   LEFT JOIN grades g ON c.grade_id = g.id"""
        if classroom_id:
            query += " WHERE s.classroom_id = ?"
        query += " ORDER BY u.last_name, u.first_name"
        students = db.execute(query, (classroom_id,) if classroom_id else ()).fetchall()
        return [dict(s) for s in students]

@router.get("/students/{student_id}")
async def get_student_detail(student_id: int, current_user: dict = Depends(require_roles("super_admin", "admin", "coach"))):
    with get_db() as db:
        student = db.execute("""SELECT s.*, u.email, u.first_name, u.last_name, u.is_active,
                                       c.name as classroom_name
                                FROM students s JOIN users u ON s.user_id = u.id
                                LEFT JOIN classrooms c ON s.classroom_id = c.id
                                WHERE s.id = ?""", (student_id,)).fetchone()
        if not student:
            raise HTTPException(status_code=404, detail="Estudiante no encontrado")
        
        mastery = db.execute("""SELECT ms.*, sk.name as skill_name, sk.category
                                FROM mastery_signals ms JOIN skills sk ON ms.skill_id = sk.id
                                WHERE ms.student_id = ? ORDER BY sk.order_index""", (student_id,)).fetchall()
        
        sessions = db.execute("""SELECT ds.*, sk.name as skill_name
                                 FROM daily_sessions ds LEFT JOIN skills sk ON ds.target_skill_id = sk.id
                                 WHERE ds.student_id = ? ORDER BY ds.started_at DESC LIMIT 20""", (student_id,)).fetchall()
        
        achievements_list = db.execute("SELECT * FROM achievements WHERE student_id = ? ORDER BY earned_at DESC", (student_id,)).fetchall()
        
        interventions_list = db.execute("""SELECT i.*, u.first_name as coach_name
                                           FROM interventions i JOIN coaches co ON i.coach_id = co.id
                                           JOIN users u ON co.user_id = u.id
                                           WHERE i.student_id = ? ORDER BY i.created_at DESC LIMIT 10""", (student_id,)).fetchall()
        
        return {
            "student": dict(student),
            "mastery": [dict(m) for m in mastery],
            "sessions": [dict(s) for s in sessions],
            "achievements": [dict(a) for a in achievements_list],
            "interventions": [dict(i) for i in interventions_list]
        }

@router.post("/students")
async def create_student(req: StudentCreate, current_user: dict = Depends(require_roles("super_admin", "admin"))):
    with get_db() as db:
        existing = db.execute("SELECT id FROM users WHERE email = ?", (req.email,)).fetchone()
        if existing:
            raise HTTPException(status_code=400, detail="Email ya registrado")
        # Auto-assign classroom based on curriculum_level if not specified
        classroom_id = req.classroom_id
        if classroom_id is None and req.curriculum_level:
            if req.curriculum_level == 'kinder':
                row = db.execute("SELECT c.id FROM classrooms c JOIN grades g ON c.grade_id = g.id WHERE g.level = 0 LIMIT 1").fetchone()
            else:
                row = db.execute("SELECT c.id FROM classrooms c JOIN grades g ON c.grade_id = g.id WHERE g.level > 0 LIMIT 1").fetchone()
            if row:
                classroom_id = row[0]
        db.execute("INSERT INTO users (email, password_hash, role, first_name, last_name) VALUES (?, ?, 'student', ?, ?)",
                   (req.email, hash_password(req.password), req.first_name, req.last_name))
        uid = db.execute("SELECT last_insert_rowid()").fetchone()[0]
        db.execute("INSERT INTO students (user_id, classroom_id, nickname, age, interests) VALUES (?, ?, ?, ?, ?)",
                   (uid, classroom_id, req.first_name, req.age, req.interests))
        sid = db.execute("SELECT last_insert_rowid()").fetchone()[0]
        db.execute("INSERT INTO audit_log (user_id, action, entity_type, entity_id, details) VALUES (?, ?, ?, ?, ?)",
                   (current_user["user_id"], "create", "student", sid, f"{req.first_name} {req.last_name}"))
        return {"id": sid, "message": "Estudiante creado"}

@router.put("/students/{student_id}")
async def update_student(student_id: int, req: StudentCreate, current_user: dict = Depends(require_roles("super_admin", "admin"))):
    with get_db() as db:
        student = db.execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()
        if not student:
            raise HTTPException(status_code=404, detail="Estudiante no encontrado")
        db.execute("UPDATE users SET first_name=?, last_name=? WHERE id=?",
                   (req.first_name, req.last_name, student["user_id"]))
        db.execute("UPDATE students SET classroom_id=?, age=?, interests=? WHERE id=?",
                   (req.classroom_id, req.age, req.interests, student_id))
        db.execute("INSERT INTO audit_log (user_id, action, entity_type, entity_id, details) VALUES (?, ?, ?, ?, ?)",
                   (current_user["user_id"], "update", "student", student_id, f"{req.first_name} {req.last_name}"))
        return {"message": "Estudiante actualizado"}

# ---- Coaches CRUD ----
@router.get("/coaches")
async def list_coaches(current_user: dict = Depends(require_roles("super_admin", "admin"))):
    with get_db() as db:
        coaches = db.execute("""SELECT co.*, u.email, u.first_name, u.last_name, u.is_active,
                                       c.name as classroom_name
                                FROM coaches co JOIN users u ON co.user_id = u.id
                                LEFT JOIN classrooms c ON co.classroom_id = c.id
                                ORDER BY u.last_name""").fetchall()
        return [dict(c) for c in coaches]

@router.post("/coaches")
async def create_coach(req: CoachCreate, current_user: dict = Depends(require_roles("super_admin", "admin"))):
    with get_db() as db:
        existing = db.execute("SELECT id FROM users WHERE email = ?", (req.email,)).fetchone()
        if existing:
            raise HTTPException(status_code=400, detail="Email ya registrado")
        db.execute("INSERT INTO users (email, password_hash, role, first_name, last_name) VALUES (?, ?, 'coach', ?, ?)",
                   (req.email, hash_password(req.password), req.first_name, req.last_name))
        uid = db.execute("SELECT last_insert_rowid()").fetchone()[0]
        db.execute("INSERT INTO coaches (user_id, classroom_id, specialization) VALUES (?, ?, ?)",
                   (uid, req.classroom_id, req.specialization))
        cid = db.execute("SELECT last_insert_rowid()").fetchone()[0]
        db.execute("INSERT INTO audit_log (user_id, action, entity_type, entity_id, details) VALUES (?, ?, ?, ?, ?)",
                   (current_user["user_id"], "create", "coach", cid, f"{req.first_name} {req.last_name}"))
        return {"id": cid, "message": "Coach creado"}

# ---- Parents CRUD ----
@router.get("/parents")
async def list_parents(current_user: dict = Depends(require_roles("super_admin", "admin"))):
    with get_db() as db:
        parents_list = db.execute("""SELECT p.*, u.email, u.first_name, u.last_name, u.is_active
                                FROM parents p JOIN users u ON p.user_id = u.id
                                ORDER BY u.last_name""").fetchall()
        result = []
        for p in parents_list:
            pd = dict(p)
            children = db.execute("""SELECT s.id, u.first_name, u.last_name 
                                     FROM parent_students ps JOIN students s ON ps.student_id = s.id
                                     JOIN users u ON s.user_id = u.id WHERE ps.parent_id = ?""", (p["id"],)).fetchall()
            pd["children"] = [dict(c) for c in children]
            result.append(pd)
        return result

@router.post("/parents")
async def create_parent(req: ParentCreate, current_user: dict = Depends(require_roles("super_admin", "admin"))):
    with get_db() as db:
        existing = db.execute("SELECT id FROM users WHERE email = ?", (req.email,)).fetchone()
        if existing:
            raise HTTPException(status_code=400, detail="Email ya registrado")
        db.execute("INSERT INTO users (email, password_hash, role, first_name, last_name) VALUES (?, ?, 'parent', ?, ?)",
                   (req.email, hash_password(req.password), req.first_name, req.last_name))
        uid = db.execute("SELECT last_insert_rowid()").fetchone()[0]
        db.execute("INSERT INTO parents (user_id, phone) VALUES (?, ?)", (uid, req.phone))
        pid = db.execute("SELECT last_insert_rowid()").fetchone()[0]
        for sid in req.student_ids:
            db.execute("INSERT INTO parent_students (parent_id, student_id) VALUES (?, ?)", (pid, sid))
        db.execute("INSERT INTO audit_log (user_id, action, entity_type, entity_id, details) VALUES (?, ?, ?, ?, ?)",
                   (current_user["user_id"], "create", "parent", pid, f"{req.first_name} {req.last_name}"))
        return {"id": pid, "message": "Padre creado"}

# ---- Skills ----
@router.get("/skills")
async def list_skills(current_user: dict = Depends(require_roles("super_admin", "admin", "coach"))):
    with get_db() as db:
        skills = db.execute("SELECT * FROM skills ORDER BY order_index").fetchall()
        return [dict(s) for s in skills]

# ---- Lessons ----
@router.get("/lessons")
async def list_lessons(current_user: dict = Depends(require_roles("super_admin", "admin", "coach"))):
    with get_db() as db:
        lessons = db.execute("""SELECT l.*, s.name as skill_name, s.category
                                FROM lessons l JOIN skills s ON l.skill_id = s.id
                                ORDER BY s.order_index""").fetchall()
        return [dict(l) for l in lessons]

@router.put("/lessons/{lesson_id}/publish")
async def toggle_lesson(lesson_id: int, current_user: dict = Depends(require_roles("super_admin", "admin"))):
    with get_db() as db:
        lesson = db.execute("SELECT * FROM lessons WHERE id = ?", (lesson_id,)).fetchone()
        if not lesson:
            raise HTTPException(status_code=404, detail="Lección no encontrada")
        new_status = 0 if lesson["is_published"] else 1
        db.execute("UPDATE lessons SET is_published = ? WHERE id = ?", (new_status, lesson_id))
        db.execute("INSERT INTO audit_log (user_id, action, entity_type, entity_id, details) VALUES (?, ?, ?, ?, ?)",
                   (current_user["user_id"], "toggle_publish", "lesson", lesson_id, f"published={new_status}"))
        return {"message": "Estado actualizado", "is_published": bool(new_status)}

# ---- Audit Log ----
@router.get("/audit-log")
async def get_audit_log(limit: int = 50, current_user: dict = Depends(require_roles("super_admin", "admin"))):
    with get_db() as db:
        logs = db.execute("""SELECT al.*, u.first_name, u.last_name, u.email
                             FROM audit_log al LEFT JOIN users u ON al.user_id = u.id
                             ORDER BY al.created_at DESC LIMIT ?""", (limit,)).fetchall()
        return [dict(l) for l in logs]

# ---- CSV Export ----
@router.get("/export/students")
async def export_students_csv(current_user: dict = Depends(require_roles("super_admin", "admin"))):
    with get_db() as db:
        students = db.execute("""SELECT s.id, u.first_name, u.last_name, u.email, s.age, s.interests,
                                        s.placement_test_completed, s.placement_test_score,
                                        c.name as classroom, c.group_type
                                 FROM students s JOIN users u ON s.user_id = u.id
                                 LEFT JOIN classrooms c ON s.classroom_id = c.id
                                 ORDER BY u.last_name""").fetchall()
        
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["ID", "Nombre", "Apellido", "Email", "Edad", "Intereses", "Placement Test", "Score", "Salón", "Grupo"])
        for s in students:
            writer.writerow([s["id"], s["first_name"], s["last_name"], s["email"], s["age"],
                           s["interests"], s["placement_test_completed"], s["placement_test_score"],
                           s["classroom"], s["group_type"]])
        
        output.seek(0)
        return StreamingResponse(output, media_type="text/csv",
                                headers={"Content-Disposition": "attachment; filename=estudiantes.csv"})

@router.get("/export/mastery")
async def export_mastery_csv(current_user: dict = Depends(require_roles("super_admin", "admin"))):
    with get_db() as db:
        data = db.execute("""SELECT ms.student_id, u.first_name, u.last_name, sk.name as skill_name,
                                    sk.category, ms.mastery_level, ms.attempts_count, ms.correct_count, ms.last_practiced
                             FROM mastery_signals ms
                             JOIN students s ON ms.student_id = s.id
                             JOIN users u ON s.user_id = u.id
                             JOIN skills sk ON ms.skill_id = sk.id
                             ORDER BY u.last_name, sk.order_index""").fetchall()
        
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Student ID", "Nombre", "Apellido", "Skill", "Categoría", "Mastery Level", "Intentos", "Correctos", "Última Práctica"])
        for d in data:
            writer.writerow([d["student_id"], d["first_name"], d["last_name"], d["skill_name"],
                           d["category"], d["mastery_level"], d["attempts_count"], d["correct_count"], d["last_practiced"]])
        
        output.seek(0)
        return StreamingResponse(output, media_type="text/csv",
                                headers={"Content-Disposition": "attachment; filename=mastery.csv"})

# ---- Invitations ----
@router.get("/invitations")
async def list_invitations(current_user: dict = Depends(require_roles("super_admin", "admin"))):
    with get_db() as db:
        invitations = db.execute("""SELECT i.*, u.first_name as invited_by_name, u.last_name as invited_by_last
                                    FROM invitations i
                                    LEFT JOIN users u ON i.invited_by = u.id
                                    ORDER BY i.created_at DESC""").fetchall()
        return [dict(inv) for inv in invitations]

@router.post("/invitations")
async def create_invitation(req: InvitationCreate, current_user: dict = Depends(require_roles("super_admin", "admin"))):
    if req.role not in ("admin", "coach", "parent", "student"):
        raise HTTPException(status_code=400, detail="Rol invalido")
    
    with get_db() as db:
        # Check if email already exists as user
        existing_user = db.execute("SELECT id FROM users WHERE email = ?", (req.email,)).fetchone()
        if existing_user:
            raise HTTPException(status_code=400, detail="Este email ya tiene una cuenta registrada")
        
        # Check if there's already a pending invitation for this email
        existing_inv = db.execute("SELECT id FROM invitations WHERE email = ? AND status = 'pending'", (req.email,)).fetchone()
        if existing_inv:
            raise HTTPException(status_code=400, detail="Ya existe una invitacion pendiente para este email")
        
        token = str(uuid.uuid4())
        expires_at = (datetime.now() + timedelta(days=7)).isoformat()
        
        db.execute("""INSERT INTO invitations (email, role, first_name, last_name, status, invited_by, token, curriculum_level, classroom_id, expires_at)
                     VALUES (?, ?, ?, ?, 'pending', ?, ?, ?, ?, ?)""",
                   (req.email, req.role, req.first_name, req.last_name, current_user["user_id"], token, req.curriculum_level, req.classroom_id, expires_at))
        inv_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
        
        db.execute("INSERT INTO audit_log (user_id, action, entity_type, entity_id, details) VALUES (?, ?, ?, ?, ?)",
                   (current_user["user_id"], "invite", "invitation", inv_id, f"{req.email} ({req.role})"))
        
        return {"id": inv_id, "token": token, "message": f"Invitacion enviada a {req.email}"}

@router.post("/invitations/{invitation_id}/resend")
async def resend_invitation(invitation_id: int, current_user: dict = Depends(require_roles("super_admin", "admin"))):
    with get_db() as db:
        inv = db.execute("SELECT * FROM invitations WHERE id = ?", (invitation_id,)).fetchone()
        if not inv:
            raise HTTPException(status_code=404, detail="Invitacion no encontrada")
        if inv["status"] != "pending":
            raise HTTPException(status_code=400, detail="Solo se pueden reenviar invitaciones pendientes")
        
        # Refresh expiry
        new_token = str(uuid.uuid4())
        new_expires = (datetime.now() + timedelta(days=7)).isoformat()
        db.execute("UPDATE invitations SET token = ?, expires_at = ? WHERE id = ?",
                   (new_token, new_expires, invitation_id))
        
        db.execute("INSERT INTO audit_log (user_id, action, entity_type, entity_id, details) VALUES (?, ?, ?, ?, ?)",
                   (current_user["user_id"], "resend_invite", "invitation", invitation_id, inv["email"]))
        
        return {"message": f"Invitacion reenviada a {inv['email']}", "token": new_token}

@router.post("/invitations/{invitation_id}/revoke")
async def revoke_invitation(invitation_id: int, current_user: dict = Depends(require_roles("super_admin", "admin"))):
    with get_db() as db:
        inv = db.execute("SELECT * FROM invitations WHERE id = ?", (invitation_id,)).fetchone()
        if not inv:
            raise HTTPException(status_code=404, detail="Invitacion no encontrada")
        if inv["status"] != "pending":
            raise HTTPException(status_code=400, detail="Solo se pueden revocar invitaciones pendientes")
        
        db.execute("UPDATE invitations SET status = 'revoked' WHERE id = ?", (invitation_id,))
        
        db.execute("INSERT INTO audit_log (user_id, action, entity_type, entity_id, details) VALUES (?, ?, ?, ?, ?)",
                   (current_user["user_id"], "revoke_invite", "invitation", invitation_id, inv["email"]))
        
        return {"message": "Invitacion revocada"}

@router.post("/invitations/{invitation_id}/accept")
async def accept_invitation(invitation_id: int, current_user: dict = Depends(require_roles("super_admin", "admin"))):
    """Accept an invitation and create the user account"""
    with get_db() as db:
        inv = db.execute("SELECT * FROM invitations WHERE id = ?", (invitation_id,)).fetchone()
        if not inv:
            raise HTTPException(status_code=404, detail="Invitacion no encontrada")
        if inv["status"] != "pending":
            raise HTTPException(status_code=400, detail="Esta invitacion ya no es valida")
        
        # Check expiry
        if inv["expires_at"] and datetime.fromisoformat(inv["expires_at"]) < datetime.now():
            db.execute("UPDATE invitations SET status = 'expired' WHERE id = ?", (invitation_id,))
            raise HTTPException(status_code=400, detail="La invitacion ha expirado")
        
        # Check if email already registered
        existing = db.execute("SELECT id FROM users WHERE email = ?", (inv["email"],)).fetchone()
        if existing:
            raise HTTPException(status_code=400, detail="Este email ya tiene una cuenta")
        
        # Create user with default password
        default_password = "welcome123"
        role = inv["role"] if inv["role"] != "admin" else "admin"
        db.execute("INSERT INTO users (email, password_hash, role, first_name, last_name) VALUES (?, ?, ?, ?, ?)",
                   (inv["email"], hash_password(default_password), role, inv["first_name"] or "Nuevo", inv["last_name"] or "Usuario"))
        uid = db.execute("SELECT last_insert_rowid()").fetchone()[0]
        
        # Create role-specific record
        if inv["role"] == "student":
            classroom_id = inv["classroom_id"]
            db.execute("INSERT INTO students (user_id, classroom_id, nickname, age) VALUES (?, ?, ?, ?)",
                       (uid, classroom_id, inv["first_name"] or "Nuevo", 9 if inv["curriculum_level"] == "4to_grado" else 5))
        elif inv["role"] == "coach":
            db.execute("INSERT INTO coaches (user_id, classroom_id, specialization) VALUES (?, ?, ?)",
                       (uid, inv["classroom_id"], "Matematicas"))
        elif inv["role"] == "parent":
            db.execute("INSERT INTO parents (user_id, phone) VALUES (?, ?)", (uid, ""))
        
        # Mark invitation as accepted
        db.execute("UPDATE invitations SET status = 'accepted', accepted_at = datetime('now') WHERE id = ?", (invitation_id,))
        
        return {"message": f"Cuenta creada para {inv['email']}. Password temporal: {default_password}", "user_id": uid}

# ---- Testing / Debug ----
@router.post("/seed-flow-questions")
async def seed_flow_questions(current_user: dict = Depends(require_roles("super_admin", "admin"))):
    """Seed exercise questions for skills 1-5 (needed for Flow Engine testing). Idempotent."""
    questions = [
        # Skill 1: Lectura de numeros hasta 10,000
        (1, "Como se escribe el numero dos mil quinientos?", "multiple_choice",
         '["2,500","2,050","2,005","250"]', "2,500", "Dos mil = 2000, quinientos = 500", "2,500", 1, '["general"]'),
        (1, "Cual de estos numeros es ocho mil trescientos doce?", "multiple_choice",
         '["8,312","8,132","8,321","3,812"]', "8,312", "Ocho mil=8000, trescientos=300, doce=12", "8,312", 1, '["general"]'),
        (1, "Como se lee el numero 4,670?", "multiple_choice",
         '["Cuatro mil seiscientos setenta","Cuatro mil sesenta y siete","Cuarenta y seis mil setenta","Cuatro mil setecientos sesenta"]',
         "Cuatro mil seiscientos setenta", "4000+600+70", "Cuatro mil seiscientos setenta", 1, '["general"]'),
        (1, "Que numero es mil novecientos noventa y nueve?", "numeric", '[]', "1999",
         "Mil=1000, novecientos=900, noventa=90, nueve=9", "1,999", 1, '["general"]'),
        (1, "Como se escribe seis mil cuatrocientos?", "numeric", '[]', "6400",
         "Seis mil=6000, cuatrocientos=400", "6,400", 1, '["general"]'),
        (1, "Cual numero es mayor: 3,210 o 3,120?", "multiple_choice",
         '["3,210","3,120","Son iguales","No se puede saber"]', "3,210",
         "Compara digito por digito", "3,210 > 3,120", 1, '["general"]'),
        (1, "Como se lee 7,005?", "multiple_choice",
         '["Siete mil cinco","Setecientos cinco","Siete mil cincuenta","Siete mil quinientos"]',
         "Siete mil cinco", "7000+5", "Siete mil cinco", 2, '["general"]'),
        (1, "Escribe en numeros: nueve mil ciento cuarenta y tres", "numeric", '[]', "9143",
         "9000+100+40+3", "9,143", 2, '["general"]'),
        (1, "Que numero es cinco mil ochocientos sesenta?", "numeric", '[]', "5860",
         "5000+800+60", "5,860", 2, '["general"]'),
        (1, "Como se escribe tres mil setecientos veintiuno?", "numeric", '[]', "3721",
         "3000+700+20+1", "3,721", 2, '["general"]'),
        # Skill 2: Valor posicional
        (2, "En el numero 4,529, que digito esta en las unidades?", "multiple_choice",
         '["4","5","2","9"]', "9", "Las unidades son el ultimo digito", "9 esta en las unidades", 1, '["general"]'),
        (2, "En 3,847, que digito esta en las decenas?", "multiple_choice",
         '["3","8","4","7"]', "4", "Las decenas son el segundo digito de derecha a izquierda", "4 esta en las decenas", 1, '["general"]'),
        (2, "En 6,215, que digito esta en los millares?", "multiple_choice",
         '["6","2","1","5"]', "6", "Los millares son el primer digito", "6 esta en los millares", 1, '["general"]'),
        (2, "Cual es el valor del 3 en el numero 2,345?", "multiple_choice",
         '["3","30","300","3000"]', "300", "El 3 esta en la posicion de las centenas", "3 centenas = 300", 2, '["general"]'),
        (2, "Cual es el valor del 7 en el numero 7,102?", "multiple_choice",
         '["7","70","700","7000"]', "7000", "El 7 esta en la posicion de los millares", "7 millares = 7,000", 2, '["general"]'),
        (2, "En el numero 8,463, cual digito tiene el mayor valor?", "multiple_choice",
         '["8","4","6","3"]', "8", "El digito en la posicion mas alta tiene el mayor valor", "8 millares = 8,000", 2, '["general"]'),
        (2, "Que numero se forma con 5 millares, 3 centenas, 2 decenas y 7 unidades?", "numeric", '[]', "5327",
         "5000+300+20+7", "5,327", 2, '["general"]'),
        (2, "Descompone 4,896: cuantas centenas hay?", "numeric", '[]', "8",
         "En 4,896 el digito de las centenas es 8", "8 centenas", 1, '["general"]'),
        (2, "Si cambias el digito de las decenas en 1,234 por un 7, que numero obtienes?", "numeric", '[]', "1274",
         "Cambia el 3 (decenas) por 7", "1,274", 3, '["general"]'),
        (2, "En 9,081, cuantas decenas hay?", "numeric", '[]', "8",
         "El digito de las decenas es 8", "8 decenas", 1, '["general"]'),
        # Skill 3: Comparacion de numeros
        (3, "Cual simbolo va entre 2,345 __ 2,435?", "multiple_choice",
         '["<",">","=","No se sabe"]', "<", "Compara digito por digito", "2,345 < 2,435", 1, '["general"]'),
        (3, "Cual es mayor: 5,678 o 5,687?", "multiple_choice",
         '["5,678","5,687","Son iguales","No se sabe"]', "5,687",
         "Compara las decenas: 8 vs 7... no, las centenas son iguales, compara decenas", "5,687 > 5,678", 1, '["general"]'),
        (3, "Ordena de menor a mayor: 1,200 y 1,020", "multiple_choice",
         '["1,020 < 1,200","1,200 < 1,020","Son iguales","1,020 = 1,200"]', "1,020 < 1,200",
         "Compara los digitos", "1,020 < 1,200", 1, '["general"]'),
        (3, "7,999 __ 8,000. Que simbolo va?", "multiple_choice",
         '["<",">","=","No se sabe"]', "<", "7 mil es menos que 8 mil", "7,999 < 8,000", 2, '["general"]'),
        (3, "Cual es el menor: 3,450, 3,405, 3,540?", "multiple_choice",
         '["3,450","3,405","3,540","Son iguales"]', "3,405",
         "Compara las centenas", "3,405 es el menor", 2, '["general"]'),
        (3, "4,100 __ 4,100. Que simbolo va?", "multiple_choice",
         '["<",">","=","No se sabe"]', "=", "Son el mismo numero", "4,100 = 4,100", 1, '["general"]'),
        (3, "Cual es mayor: 9,999 o 10,000?", "multiple_choice",
         '["9,999","10,000","Son iguales","No se sabe"]', "10,000",
         "10,000 tiene 5 digitos, 9,999 tiene 4", "10,000 > 9,999", 2, '["general"]'),
        (3, "Pon >, < o =: 6,543 __ 6,534", "multiple_choice",
         '["<",">","=","No se sabe"]', ">", "Las decenas: 4 vs 3", "6,543 > 6,534", 2, '["general"]'),
        (3, "Cual numero esta mas cerca de 5,000: 4,800 o 5,300?", "multiple_choice",
         '["4,800","5,300","Estan igual de cerca","No se sabe"]', "4,800",
         "4800 esta a 200 de 5000, 5300 esta a 300", "4,800 (diferencia de 200)", 3, '["general"]'),
        (3, "Cual es mayor: 2,999 o 3,001?", "multiple_choice",
         '["2,999","3,001","Son iguales","No se sabe"]', "3,001",
         "3 mil es mas que 2 mil", "3,001 > 2,999", 1, '["general"]'),
        # Skill 4: Ordenar numeros
        (4, "Ordena de menor a mayor: 500, 300, 700", "multiple_choice",
         '["300, 500, 700","500, 300, 700","700, 500, 300","300, 700, 500"]', "300, 500, 700",
         "Encuentra el mas pequeno primero", "300 < 500 < 700", 1, '["general"]'),
        (4, "Ordena de mayor a menor: 1,234, 4,321, 2,143", "multiple_choice",
         '["4,321, 2,143, 1,234","1,234, 2,143, 4,321","4,321, 1,234, 2,143","2,143, 4,321, 1,234"]',
         "4,321, 2,143, 1,234", "Encuentra el mas grande primero", "4,321 > 2,143 > 1,234", 2, '["general"]'),
        (4, "Cual numero va entre 2,340 y 2,360?", "multiple_choice",
         '["2,330","2,350","2,370","2,300"]', "2,350",
         "Busca un numero mayor que 2340 y menor que 2360", "2,340 < 2,350 < 2,360", 1, '["general"]'),
        (4, "Ordena: 8,100, 8,010, 8,001 de menor a mayor", "multiple_choice",
         '["8,001, 8,010, 8,100","8,010, 8,001, 8,100","8,100, 8,010, 8,001","8,001, 8,100, 8,010"]',
         "8,001, 8,010, 8,100", "Compara digito por digito", "8,001 < 8,010 < 8,100", 2, '["general"]'),
        (4, "Que numero va justo despues de 3,999?", "numeric", '[]', "4000",
         "Suma 1 a 3,999", "3,999 + 1 = 4,000", 1, '["general"]'),
        (4, "Que numero va justo antes de 7,000?", "numeric", '[]', "6999",
         "Resta 1 a 7,000", "7,000 - 1 = 6,999", 1, '["general"]'),
        (4, "Ordena de menor a mayor: 5,050, 5,500, 5,005", "multiple_choice",
         '["5,005, 5,050, 5,500","5,050, 5,005, 5,500","5,500, 5,050, 5,005","5,005, 5,500, 5,050"]',
         "5,005, 5,050, 5,500", "Compara centenas", "5,005 < 5,050 < 5,500", 2, '["general"]'),
        (4, "Que numero esta entre 4,500 y 4,600?", "multiple_choice",
         '["4,400","4,550","4,700","4,300"]', "4,550",
         "Busca mayor que 4500 y menor que 4600", "4,500 < 4,550 < 4,600", 1, '["general"]'),
        (4, "Ordena de mayor a menor: 9,876, 9,678, 9,768", "multiple_choice",
         '["9,876, 9,768, 9,678","9,678, 9,768, 9,876","9,876, 9,678, 9,768","9,768, 9,876, 9,678"]',
         "9,876, 9,768, 9,678", "Compara centenas: 8>7>6", "9,876 > 9,768 > 9,678", 2, '["general"]'),
        (4, "Cual es el tercer numero en orden de menor a mayor: 100, 1000, 10, 10000?", "numeric", '[]', "1000",
         "Ordena: 10, 100, 1000, 10000", "El tercero es 1,000", 2, '["general"]'),
        # Skill 5: Redondeo
        (5, "Redondea 347 a la decena mas cercana", "numeric", '[]', "350",
         "Mira el digito de las unidades: 7>=5, sube", "347 -> 350", 1, '["general"]'),
        (5, "Redondea 823 a la centena mas cercana", "numeric", '[]', "800",
         "Mira el digito de las decenas: 2<5, baja", "823 -> 800", 1, '["general"]'),
        (5, "Redondea 1,450 a la centena mas cercana", "multiple_choice",
         '["1,400","1,500","1,000","2,000"]', "1,500",
         "5 en las decenas = sube", "1,450 -> 1,500", 2, '["general"]'),
        (5, "Redondea 6,789 a la decena mas cercana", "numeric", '[]', "6790",
         "9>=5, sube la decena", "6,789 -> 6,790", 2, '["general"]'),
        (5, "Redondea 2,550 a la centena mas cercana", "numeric", '[]', "2600",
         "5 en las decenas = sube", "2,550 -> 2,600", 2, '["general"]'),
        (5, "Redondea 4,321 a la decena mas cercana", "numeric", '[]', "4320",
         "1<5, baja", "4,321 -> 4,320", 1, '["general"]'),
        (5, "Redondea 9,950 a la centena mas cercana", "numeric", '[]', "10000",
         "5 en las decenas = sube: 9,900+100=10,000", "9,950 -> 10,000", 3, '["general"]'),
        (5, "Redondea 3,333 a la centena mas cercana", "numeric", '[]', "3300",
         "3<5 en las decenas, baja", "3,333 -> 3,300", 1, '["general"]'),
        (5, "Redondea 7,865 a la decena mas cercana", "numeric", '[]', "7870",
         "5>=5, sube", "7,865 -> 7,870", 2, '["general"]'),
        (5, "Redondea 1,149 a la centena mas cercana", "multiple_choice",
         '["1,100","1,200","1,000","1,150"]', "1,100",
         "4<5, baja", "1,149 -> 1,100", 1, '["general"]'),
    ]
    with get_db() as db:
        inserted = 0
        for q in questions:
            existing = db.execute(
                "SELECT id FROM questions WHERE skill_id = ? AND question_text = ? AND is_placement = 0",
                (q[0], q[1])
            ).fetchone()
            if not existing:
                db.execute(
                    """INSERT INTO questions (skill_id, question_text, question_type, options, correct_answer,
                       hint, explanation, difficulty, is_placement, interest_tags)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, ?)""", q
                )
                inserted += 1
        db.execute(
            "INSERT INTO audit_log (user_id, action, entity_type, entity_id, details) VALUES (?, ?, ?, ?, ?)",
            (current_user["user_id"], "seed_flow_questions", "questions", 0,
             f"Seeded {inserted} exercise questions for skills 1-5")
        )
        return {"message": f"Inserted {inserted} new exercise questions for skills 1-5"}

@router.post("/reset-student-session/{student_id}")
async def reset_student_session(student_id: int, current_user: dict = Depends(require_roles("super_admin", "admin"))):
    """Reset today's session for a student so they can start fresh. Admin-only."""
    with get_db() as db:
        student = db.execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()
        if not student:
            raise HTTPException(status_code=404, detail="Estudiante no encontrado")
        
        # Delete today's sessions and their attempts
        sessions = db.execute(
            "SELECT id FROM daily_sessions WHERE student_id = ? AND session_date = date('now')",
            (student_id,)
        ).fetchall()
        for s in sessions:
            db.execute("DELETE FROM session_attempts WHERE session_id = ?", (s["id"],))
        db.execute(
            "DELETE FROM daily_sessions WHERE student_id = ? AND session_date = date('now')",
            (student_id,)
        )
        
        # Reset mastery theta back to initial for fresh testing
        db.execute(
            "UPDATE mastery_signals SET theta = 1000.0, strength = 1.0 WHERE student_id = ?",
            (student_id,)
        )
        
        # Clean up flow events from today
        db.execute(
            "DELETE FROM flow_events WHERE student_id = ? AND ts >= date('now')",
            (student_id,)
        )
        
        db.execute(
            "INSERT INTO audit_log (user_id, action, entity_type, entity_id, details) VALUES (?, ?, ?, ?, ?)",
            (current_user["user_id"], "reset_session", "student", student_id, "Reset daily session for testing")
        )
        
        return {"message": f"Sesión del estudiante {student_id} reiniciada"}
