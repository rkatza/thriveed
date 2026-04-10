from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.database import get_db
from app.auth import get_current_user, require_roles
import json

router = APIRouter(prefix="/api/coach", tags=["coach"])

class InterventionCreate(BaseModel):
    student_id: int
    session_id: Optional[int] = None
    tag: str
    notes: Optional[str] = None

class MessageCreate(BaseModel):
    parent_user_id: int
    student_id: int
    subject: str
    body: str

def get_coach(current_user):
    with get_db() as db:
        coach = db.execute("SELECT * FROM coaches WHERE user_id = ?", (current_user["user_id"],)).fetchone()
        if not coach:
            raise HTTPException(status_code=404, detail="Perfil de coach no encontrado")
        return dict(coach)

# ---- Live Classroom View ----
@router.get("/classroom/live")
async def classroom_live(current_user: dict = Depends(require_roles("coach"))):
    coach = get_coach(current_user)
    with get_db() as db:
        classroom_id = coach["classroom_id"]
        if not classroom_id:
            return {"students": [], "classroom": None}
        
        classroom = db.execute("SELECT * FROM classrooms WHERE id = ?", (classroom_id,)).fetchone()
        
        students = db.execute("""
            SELECT s.id, s.nickname, s.avatar_url, u.first_name, u.last_name,
                   ds.id as session_id, ds.status as session_status, ds.mission_title,
                   ds.total_questions, ds.correct_answers, ds.active_time_seconds,
                   ds.target_skill_id, sk.name as skill_name,
                   hr.id as help_request_id, hr.status as help_status
            FROM students s
            JOIN users u ON s.user_id = u.id
            LEFT JOIN daily_sessions ds ON ds.student_id = s.id AND ds.session_date = date('now')
            LEFT JOIN skills sk ON ds.target_skill_id = sk.id
            LEFT JOIN help_requests hr ON hr.student_id = s.id AND hr.status = 'pending'
            WHERE s.classroom_id = ?
            ORDER BY u.first_name
        """, (classroom_id,)).fetchall()
        
        result = []
        for s in students:
            sd = dict(s)
            # Determine status indicator
            if sd["help_request_id"]:
                sd["indicator"] = "red"
                sd["indicator_text"] = "Pidiendo ayuda"
            elif sd["session_status"] == "completed":
                sd["indicator"] = "green"
                sd["indicator_text"] = "Sesión completada"
            elif sd["session_status"] == "in_progress":
                accuracy = (sd["correct_answers"] / sd["total_questions"] * 100) if sd["total_questions"] > 0 else 100
                if accuracy < 50:
                    sd["indicator"] = "yellow"
                    sd["indicator_text"] = f"Dificultad ({accuracy:.0f}% precisión)"
                else:
                    sd["indicator"] = "green"
                    sd["indicator_text"] = f"Trabajando bien ({accuracy:.0f}%)"
            elif sd["session_status"] == "paused":
                sd["indicator"] = "yellow"
                sd["indicator_text"] = "Sesión pausada"
            else:
                sd["indicator"] = "gray"
                sd["indicator_text"] = "Sin sesión activa"
            result.append(sd)
        
        return {
            "classroom": dict(classroom) if classroom else None,
            "students": result,
            "stats": {
                "total": len(result),
                "active": sum(1 for s in result if s["indicator"] == "green"),
                "warning": sum(1 for s in result if s["indicator"] == "yellow"),
                "alert": sum(1 for s in result if s["indicator"] == "red"),
                "inactive": sum(1 for s in result if s["indicator"] == "gray")
            }
        }

@router.get("/student/{student_id}/detail")
async def student_detail(student_id: int, current_user: dict = Depends(require_roles("coach", "super_admin", "admin"))):
    with get_db() as db:
        student = db.execute("""SELECT s.*, u.first_name, u.last_name, u.email
                                FROM students s JOIN users u ON s.user_id = u.id
                                WHERE s.id = ?""", (student_id,)).fetchone()
        if not student:
            raise HTTPException(status_code=404, detail="Estudiante no encontrado")
        
        # Current session
        session = db.execute("""SELECT ds.*, sk.name as skill_name
                                FROM daily_sessions ds LEFT JOIN skills sk ON ds.target_skill_id = sk.id
                                WHERE ds.student_id = ? AND ds.session_date = date('now')
                                ORDER BY ds.started_at DESC LIMIT 1""",
                             (student_id,)).fetchone()
        
        # Recent attempts in current session
        attempts = []
        if session:
            attempts = db.execute("""SELECT sa.*, q.question_text, q.correct_answer, q.hint, q.explanation, sk.name as skill_name
                                     FROM session_attempts sa
                                     JOIN questions q ON sa.question_id = q.id
                                     JOIN skills sk ON q.skill_id = sk.id
                                     WHERE sa.session_id = ?
                                     ORDER BY sa.created_at DESC""",
                                  (session["id"],)).fetchall()
        
        # Mastery map
        mastery = db.execute("""SELECT ms.*, sk.name, sk.category
                                FROM mastery_signals ms JOIN skills sk ON ms.skill_id = sk.id
                                WHERE ms.student_id = ? ORDER BY sk.order_index""",
                             (student_id,)).fetchall()
        
        # Recent interventions
        interventions_list = db.execute("""SELECT * FROM interventions WHERE student_id = ?
                                    ORDER BY created_at DESC LIMIT 10""",
                                 (student_id,)).fetchall()
        
        return {
            "student": dict(student),
            "current_session": dict(session) if session else None,
            "recent_attempts": [dict(a) for a in attempts],
            "mastery": [dict(m) for m in mastery],
            "interventions": [dict(i) for i in interventions_list]
        }

# ---- Interventions ----
@router.post("/intervention")
async def create_intervention(req: InterventionCreate, current_user: dict = Depends(require_roles("coach"))):
    coach = get_coach(current_user)
    with get_db() as db:
        db.execute("""INSERT INTO interventions (coach_id, student_id, session_id, tag, notes)
                     VALUES (?, ?, ?, ?, ?)""",
                   (coach["id"], req.student_id, req.session_id, req.tag, req.notes))
        
        # Dismiss any pending help requests for this student
        db.execute("UPDATE help_requests SET status = 'attended' WHERE student_id = ? AND status = 'pending'",
                   (req.student_id,))
        
        return {"message": "Intervención registrada"}

# ---- Daily Summary ----
@router.get("/daily-summary")
async def daily_summary(current_user: dict = Depends(require_roles("coach"))):
    coach = get_coach(current_user)
    with get_db() as db:
        classroom_id = coach["classroom_id"]
        
        sessions = db.execute("""
            SELECT ds.*, u.first_name, u.last_name, sk.name as skill_name
            FROM daily_sessions ds
            JOIN students s ON ds.student_id = s.id
            JOIN users u ON s.user_id = u.id
            LEFT JOIN skills sk ON ds.target_skill_id = sk.id
            WHERE s.classroom_id = ? AND ds.session_date = date('now')
            ORDER BY u.first_name
        """, (classroom_id,)).fetchall()
        
        total = len(sessions)
        completed = sum(1 for s in sessions if s["status"] == "completed")
        avg_time = sum(s["active_time_seconds"] for s in sessions) / total if total > 0 else 0
        avg_accuracy = sum(
            (s["correct_answers"] / s["total_questions"] * 100) if s["total_questions"] > 0 else 0
            for s in sessions
        ) / total if total > 0 else 0
        
        interventions_today = db.execute("""
            SELECT i.*, u.first_name as student_name
            FROM interventions i
            JOIN students s ON i.student_id = s.id
            JOIN users u ON s.user_id = u.id
            WHERE i.coach_id = ? AND date(i.created_at) = date('now')
        """, (coach["id"],)).fetchall()
        
        # Skills covered today
        skills_covered = db.execute("""
            SELECT DISTINCT sk.name, sk.category
            FROM daily_sessions ds
            JOIN skills sk ON ds.target_skill_id = sk.id
            JOIN students s ON ds.student_id = s.id
            WHERE s.classroom_id = ? AND ds.session_date = date('now')
        """, (classroom_id,)).fetchall()
        
        return {
            "date": "hoy",
            "sessions": [dict(s) for s in sessions],
            "summary": {
                "total_students": total,
                "completed": completed,
                "avg_time_minutes": round(avg_time / 60, 1),
                "avg_accuracy": round(avg_accuracy, 1),
                "interventions_count": len(interventions_today)
            },
            "interventions": [dict(i) for i in interventions_today],
            "skills_covered": [dict(s) for s in skills_covered]
        }

@router.get("/student/{student_id}/mastery-map")
async def student_mastery_map(student_id: int, current_user: dict = Depends(require_roles("coach", "super_admin", "admin"))):
    with get_db() as db:
        skills = db.execute("SELECT * FROM skills ORDER BY order_index").fetchall()
        mastery = db.execute("SELECT * FROM mastery_signals WHERE student_id = ?", (student_id,)).fetchall()
        mastery_dict = {m["skill_id"]: dict(m) for m in mastery}
        
        result = []
        for s in skills:
            m = mastery_dict.get(s["id"])
            result.append({
                **dict(s),
                "mastery_level": m["mastery_level"] if m else 0,
                "attempts_count": m["attempts_count"] if m else 0,
                "correct_count": m["correct_count"] if m else 0,
                "last_practiced": m["last_practiced"] if m else None,
                "status": "mastered" if m and m["mastery_level"] >= 0.9 else
                          "in_progress" if m and m["mastery_level"] > 0 else "not_started"
            })
        return result

# ---- Message to parent ----
@router.post("/message")
async def send_message_to_parent(req: MessageCreate, current_user: dict = Depends(require_roles("coach"))):
    with get_db() as db:
        db.execute("""INSERT INTO messages (sender_id, receiver_id, student_id, subject, body)
                     VALUES (?, ?, ?, ?, ?)""",
                   (current_user["user_id"], req.parent_user_id, req.student_id, req.subject, req.body))
        return {"message": "Nota enviada al padre"}

# ---- Pause student session ----
@router.post("/student/{student_id}/pause")
async def pause_student(student_id: int, current_user: dict = Depends(require_roles("coach"))):
    with get_db() as db:
        db.execute("""UPDATE daily_sessions SET status = 'paused'
                     WHERE student_id = ? AND session_date = date('now') AND status IN ('pending', 'in_progress')""",
                   (student_id,))
        return {"message": "Sesión pausada"}

@router.post("/student/{student_id}/resume")
async def resume_student(student_id: int, current_user: dict = Depends(require_roles("coach"))):
    with get_db() as db:
        db.execute("""UPDATE daily_sessions SET status = 'in_progress'
                     WHERE student_id = ? AND session_date = date('now') AND status = 'paused'""",
                   (student_id,))
        return {"message": "Sesión reanudada"}

# ---- Help Requests ----
@router.get("/help-requests")
async def get_help_requests(current_user: dict = Depends(require_roles("coach"))):
    coach = get_coach(current_user)
    with get_db() as db:
        requests = db.execute("""
            SELECT hr.*, u.first_name, u.last_name, s.avatar_url, s.nickname
            FROM help_requests hr
            JOIN students s ON hr.student_id = s.id
            JOIN users u ON s.user_id = u.id
            WHERE s.classroom_id = ? AND hr.status = 'pending'
            ORDER BY hr.created_at ASC
        """, (coach["classroom_id"],)).fetchall()
        return [dict(r) for r in requests]
