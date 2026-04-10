from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.database import get_db
from app.auth import get_current_user, require_roles
import json

router = APIRouter(prefix="/api/parent", tags=["parent"])

class MessageCreate(BaseModel):
    receiver_id: int
    student_id: int
    subject: str
    body: str

class ReportCreate(BaseModel):
    student_id: int
    body: str

def get_parent(current_user):
    with get_db() as db:
        parent = db.execute("SELECT * FROM parents WHERE user_id = ?", (current_user["user_id"],)).fetchone()
        if not parent:
            raise HTTPException(status_code=404, detail="Perfil de padre no encontrado")
        return dict(parent)

# ---- Children list ----
@router.get("/children")
async def get_children(current_user: dict = Depends(require_roles("parent"))):
    parent = get_parent(current_user)
    with get_db() as db:
        children = db.execute("""
            SELECT s.*, u.first_name, u.last_name, u.email,
                   c.name as classroom_name, g.name as grade_name
            FROM parent_students ps
            JOIN students s ON ps.student_id = s.id
            JOIN users u ON s.user_id = u.id
            LEFT JOIN classrooms c ON s.classroom_id = c.id
            LEFT JOIN grades g ON c.grade_id = g.id
            WHERE ps.parent_id = ?
        """, (parent["id"],)).fetchall()
        return [dict(c) for c in children]

# ---- Child daily summary ----
@router.get("/child/{student_id}/today")
async def child_today(student_id: int, current_user: dict = Depends(require_roles("parent"))):
    parent = get_parent(current_user)
    # Verify parent has access to this child
    with get_db() as db:
        link = db.execute("SELECT * FROM parent_students WHERE parent_id = ? AND student_id = ?",
                         (parent["id"], student_id)).fetchone()
        if not link:
            raise HTTPException(status_code=403, detail="No tienes acceso a este estudiante")
        
        student = db.execute("""SELECT s.*, u.first_name, u.last_name
                                FROM students s JOIN users u ON s.user_id = u.id
                                WHERE s.id = ?""", (student_id,)).fetchone()
        
        # Today's sessions
        sessions = db.execute("""
            SELECT ds.*, sk.name as skill_name, sk.category
            FROM daily_sessions ds
            LEFT JOIN skills sk ON ds.target_skill_id = sk.id
            WHERE ds.student_id = ? AND ds.session_date = date('now')
            ORDER BY ds.started_at DESC
        """, (student_id,)).fetchall()
        
        # Overall status
        completed = sum(1 for s in sessions if s["status"] == "completed")
        total = len(sessions)
        
        if total == 0:
            status = "sin_actividad"
            status_icon = "⏳"
        elif completed == total:
            status = "todo_bien"
            status_icon = "✅"
        else:
            # Check for alerts
            help_reqs = db.execute("SELECT COUNT(*) as c FROM help_requests WHERE student_id = ? AND status = 'pending'",
                                  (student_id,)).fetchone()["c"]
            if help_reqs > 0:
                status = "alerta"
                status_icon = "❗"
            else:
                status = "atencion"
                status_icon = "⚠️"
        
        total_time = sum(s["active_time_seconds"] for s in sessions)
        
        return {
            "student": dict(student),
            "status": status,
            "status_icon": status_icon,
            "sessions": [dict(s) for s in sessions],
            "summary": {
                "completed": completed,
                "total": total,
                "total_time_minutes": round(total_time / 60, 1),
                "skills_worked": [s["skill_name"] for s in sessions if s["skill_name"]]
            }
        }

# ---- Child weekly summary ----
@router.get("/child/{student_id}/week")
async def child_week(student_id: int, current_user: dict = Depends(require_roles("parent"))):
    parent = get_parent(current_user)
    with get_db() as db:
        link = db.execute("SELECT * FROM parent_students WHERE parent_id = ? AND student_id = ?",
                         (parent["id"], student_id)).fetchone()
        if not link:
            raise HTTPException(status_code=403, detail="No tienes acceso a este estudiante")
        
        sessions = db.execute("""
            SELECT ds.*, sk.name as skill_name
            FROM daily_sessions ds
            LEFT JOIN skills sk ON ds.target_skill_id = sk.id
            WHERE ds.student_id = ? AND ds.session_date >= date('now', '-7 days')
            ORDER BY ds.session_date DESC
        """, (student_id,)).fetchall()
        
        completed = sum(1 for s in sessions if s["status"] == "completed")
        total_time = sum(s["active_time_seconds"] for s in sessions)
        avg_accuracy = 0
        scored_sessions = [s for s in sessions if s["total_questions"] > 0]
        if scored_sessions:
            avg_accuracy = sum(s["correct_answers"] / s["total_questions"] * 100 for s in scored_sessions) / len(scored_sessions)
        
        # Skills mastered this week
        mastery_changes = db.execute("""
            SELECT sk.name, ms.mastery_level
            FROM mastery_signals ms
            JOIN skills sk ON ms.skill_id = sk.id
            WHERE ms.student_id = ? AND ms.last_practiced >= date('now', '-7 days')
            ORDER BY ms.mastery_level DESC
        """, (student_id,)).fetchall()
        
        return {
            "sessions": [dict(s) for s in sessions],
            "summary": {
                "total_sessions": len(sessions),
                "completed": completed,
                "total_time_minutes": round(total_time / 60, 1),
                "avg_accuracy": round(avg_accuracy, 1),
                "days_active": len(set(s["session_date"] for s in sessions))
            },
            "skills_progress": [dict(m) for m in mastery_changes]
        }

# ---- Child skill map ----
@router.get("/child/{student_id}/skill-map")
async def child_skill_map(student_id: int, current_user: dict = Depends(require_roles("parent"))):
    parent = get_parent(current_user)
    with get_db() as db:
        link = db.execute("SELECT * FROM parent_students WHERE parent_id = ? AND student_id = ?",
                         (parent["id"], student_id)).fetchone()
        if not link:
            raise HTTPException(status_code=403, detail="No tienes acceso a este estudiante")
        
        skills = db.execute("SELECT * FROM skills ORDER BY order_index").fetchall()
        mastery = db.execute("SELECT * FROM mastery_signals WHERE student_id = ?", (student_id,)).fetchall()
        mastery_dict = {m["skill_id"]: m["mastery_level"] for m in mastery}
        
        categories = {}
        for s in skills:
            cat = s["category"]
            if cat not in categories:
                categories[cat] = {"category": cat, "skills": [], "avg_mastery": 0}
            categories[cat]["skills"].append({
                "name": s["name"],
                "mastery_level": mastery_dict.get(s["id"], 0),
                "status": "dominado" if mastery_dict.get(s["id"], 0) >= 0.9 else
                          "practicando" if mastery_dict.get(s["id"], 0) > 0 else "por_iniciar"
            })
        
        for cat in categories.values():
            levels = [s["mastery_level"] for s in cat["skills"]]
            cat["avg_mastery"] = round(sum(levels) / len(levels) * 100, 1) if levels else 0
        
        return list(categories.values())

# ---- Timeline ----
@router.get("/child/{student_id}/timeline")
async def child_timeline(student_id: int, current_user: dict = Depends(require_roles("parent"))):
    parent = get_parent(current_user)
    with get_db() as db:
        link = db.execute("SELECT * FROM parent_students WHERE parent_id = ? AND student_id = ?",
                         (parent["id"], student_id)).fetchone()
        if not link:
            raise HTTPException(status_code=403, detail="No tienes acceso a este estudiante")
        
        events = []
        
        # Sessions
        sessions = db.execute("""SELECT ds.*, sk.name as skill_name
                                 FROM daily_sessions ds LEFT JOIN skills sk ON ds.target_skill_id = sk.id
                                 WHERE ds.student_id = ? ORDER BY ds.started_at DESC LIMIT 20""",
                              (student_id,)).fetchall()
        for s in sessions:
            events.append({
                "type": "session",
                "date": s["started_at"],
                "title": s["mission_title"] or f"Sesión: {s['skill_name']}",
                "detail": f"{'Completada' if s['status'] == 'completed' else 'En progreso'} - {s['correct_answers']}/{s['total_questions']} correctas",
                "icon": "📚"
            })
        
        # Achievements
        achievements = db.execute("SELECT * FROM achievements WHERE student_id = ? ORDER BY earned_at DESC LIMIT 10",
                                 (student_id,)).fetchall()
        for a in achievements:
            events.append({
                "type": "achievement",
                "date": a["earned_at"],
                "title": a["title"],
                "detail": a["description"],
                "icon": a["icon"]
            })
        
        # Interventions
        interventions_list = db.execute("""SELECT i.*, u.first_name as coach_name
                                    FROM interventions i JOIN coaches co ON i.coach_id = co.id
                                    JOIN users u ON co.user_id = u.id
                                    WHERE i.student_id = ? ORDER BY i.created_at DESC LIMIT 10""",
                                 (student_id,)).fetchall()
        for i in interventions_list:
            events.append({
                "type": "intervention",
                "date": i["created_at"],
                "title": f"Intervención del coach {i['coach_name']}",
                "detail": f"Motivo: {i['tag']}. {i['notes'] or ''}",
                "icon": "👩‍🏫"
            })
        
        # Sort by date
        events.sort(key=lambda x: x["date"] or "", reverse=True)
        return events

# ---- Messages ----
@router.get("/messages")
async def get_messages(current_user: dict = Depends(require_roles("parent"))):
    with get_db() as db:
        messages = db.execute("""
            SELECT m.*, 
                   su.first_name as sender_first, su.last_name as sender_last,
                   ru.first_name as receiver_first, ru.last_name as receiver_last,
                   st_u.first_name as student_first
            FROM messages m
            JOIN users su ON m.sender_id = su.id
            JOIN users ru ON m.receiver_id = ru.id
            LEFT JOIN students st ON m.student_id = st.id
            LEFT JOIN users st_u ON st.user_id = st_u.id
            WHERE m.sender_id = ? OR m.receiver_id = ?
            ORDER BY m.created_at DESC
        """, (current_user["user_id"], current_user["user_id"])).fetchall()
        
        # Mark as read
        db.execute("UPDATE messages SET is_read = 1 WHERE receiver_id = ? AND is_read = 0",
                   (current_user["user_id"],))
        
        return [dict(m) for m in messages]

@router.post("/messages")
async def send_message(req: MessageCreate, current_user: dict = Depends(require_roles("parent"))):
    with get_db() as db:
        db.execute("""INSERT INTO messages (sender_id, receiver_id, student_id, subject, body)
                     VALUES (?, ?, ?, ?, ?)""",
                   (current_user["user_id"], req.receiver_id, req.student_id, req.subject, req.body))
        return {"message": "Mensaje enviado"}

# ---- Report to director ----
@router.post("/report")
async def send_report(req: ReportCreate, current_user: dict = Depends(require_roles("parent"))):
    with get_db() as db:
        # Find admin
        admin = db.execute("SELECT id FROM users WHERE role = 'super_admin' LIMIT 1").fetchone()
        if admin:
            db.execute("""INSERT INTO messages (sender_id, receiver_id, student_id, subject, body)
                         VALUES (?, ?, ?, ?, ?)""",
                       (current_user["user_id"], admin["id"], req.student_id, "Reporte del padre", req.body))
        return {"message": "Reporte enviado al director"}
