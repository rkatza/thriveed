from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.database import get_db
from app.auth import get_current_user, require_roles
import json, random
from datetime import datetime, timezone

from app.services.flow_engine import (
    CFG,
    StreakState,
    apply_answer_to_streak,
    decayed_strength,
    elo_update,
    expected_p_correct,
    update_half_life,
    update_strength,
)
from app.services.question_selector import select_next_question
from app.services.gamification import (
    calculate_answer_xp,
    calculate_session_xp,
    check_badges,
    level_progress,
    update_streak,
    xp_to_level,
    BADGES,
    BADGE_MAP,
)

router = APIRouter(prefix="/api/student", tags=["student"])

# ---- Models ----
class ProfileUpdate(BaseModel):
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None

class InterestsUpdate(BaseModel):
    interests: list[str]

class AnswerSubmit(BaseModel):
    question_id: int
    answer: str
    time_spent_seconds: int = 0

class SessionRating(BaseModel):
    rating: int

def get_student(current_user):
    with get_db() as db:
        student = db.execute("SELECT * FROM students WHERE user_id = ?", (current_user["user_id"],)).fetchone()
        if not student:
            raise HTTPException(status_code=404, detail="Perfil de estudiante no encontrado")
        return dict(student)

# ---- Profile ----
@router.get("/profile")
async def get_profile(current_user: dict = Depends(require_roles("student"))):
    with get_db() as db:
        student = db.execute("""SELECT s.*, u.first_name, u.last_name, u.email
                                FROM students s JOIN users u ON s.user_id = u.id
                                WHERE s.user_id = ?""", (current_user["user_id"],)).fetchone()
        if not student:
            raise HTTPException(status_code=404, detail="Perfil no encontrado")
        result = dict(student)
        result["curriculum_level"] = get_student_curriculum_level(db, student["id"])
        return result

@router.put("/profile")
async def update_profile(req: ProfileUpdate, current_user: dict = Depends(require_roles("student"))):
    student = get_student(current_user)
    with get_db() as db:
        if req.nickname:
            db.execute("UPDATE students SET nickname = ? WHERE id = ?", (req.nickname, student["id"]))
        if req.avatar_url:
            db.execute("UPDATE students SET avatar_url = ? WHERE id = ?", (req.avatar_url, student["id"]))
        return {"message": "Perfil actualizado"}

@router.post("/interests")
async def update_interests(req: InterestsUpdate, current_user: dict = Depends(require_roles("student"))):
    student = get_student(current_user)
    with get_db() as db:
        db.execute("UPDATE students SET interests = ? WHERE id = ?", (json.dumps(req.interests), student["id"]))
        return {"message": "Intereses actualizados", "interests": req.interests}

# ---- Placement Test ----
@router.get("/placement-test/start")
async def start_placement_test(current_user: dict = Depends(require_roles("student"))):
    student = get_student(current_user)
    with get_db() as db:
        # Check existing in-progress test
        existing = db.execute("SELECT * FROM placement_tests WHERE student_id = ? AND status = 'in_progress'",
                             (student["id"],)).fetchone()
        if existing:
            # Return current state
            answered_ids = [r["question_id"] for r in db.execute(
                "SELECT question_id FROM placement_answers WHERE placement_test_id = ?", (existing["id"],)).fetchall()]
            next_q = get_next_placement_question(db, existing["current_difficulty"], answered_ids, student)
            return {
                "test_id": existing["id"],
                "status": "in_progress",
                "questions_answered": existing["questions_answered"],
                "current_difficulty": existing["current_difficulty"],
                "next_question": next_q
            }
        
        if student["placement_test_completed"]:
            raise HTTPException(status_code=400, detail="Ya completaste el placement test")
        
        # Create new test
        db.execute("INSERT INTO placement_tests (student_id) VALUES (?)", (student["id"],))
        test_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
        
        # Get first question (easiest)
        first_q = get_next_placement_question(db, 1, [], student)
        
        return {
            "test_id": test_id,
            "status": "in_progress",
            "questions_answered": 0,
            "current_difficulty": 1,
            "next_question": first_q
        }

@router.post("/placement-test/answer")
async def answer_placement_test(req: AnswerSubmit, current_user: dict = Depends(require_roles("student"))):
    student = get_student(current_user)
    with get_db() as db:
        test = db.execute("SELECT * FROM placement_tests WHERE student_id = ? AND status = 'in_progress'",
                         (student["id"],)).fetchone()
        if not test:
            raise HTTPException(status_code=400, detail="No hay placement test en progreso")
        
        # Check answer
        question = db.execute("SELECT * FROM questions WHERE id = ?", (req.question_id,)).fetchone()
        if not question:
            raise HTTPException(status_code=404, detail="Pregunta no encontrada")
        
        is_correct = req.answer.strip().lower() == question["correct_answer"].strip().lower()
        
        # Save answer
        db.execute("""INSERT INTO placement_answers (placement_test_id, question_id, student_answer, is_correct, time_spent_seconds)
                     VALUES (?, ?, ?, ?, ?)""",
                   (test["id"], req.question_id, req.answer, int(is_correct), req.time_spent_seconds))
        
        new_answered = test["questions_answered"] + 1
        new_correct = test["correct_answers"] + (1 if is_correct else 0)
        
        # Adaptive difficulty
        new_difficulty = test["current_difficulty"]
        if is_correct:
            new_difficulty = min(4, test["current_difficulty"] + 1)
        else:
            new_difficulty = max(1, test["current_difficulty"] - 1)
        
        db.execute("""UPDATE placement_tests SET questions_answered = ?, correct_answers = ?, current_difficulty = ?
                     WHERE id = ?""", (new_answered, new_correct, new_difficulty, test["id"]))
        
        # Update mastery for this skill
        skill_id = question["skill_id"]
        existing_mastery = db.execute("SELECT * FROM mastery_signals WHERE student_id = ? AND skill_id = ?",
                                     (student["id"], skill_id)).fetchone()
        if existing_mastery:
            new_attempts = existing_mastery["attempts_count"] + 1
            new_correct_count = existing_mastery["correct_count"] + (1 if is_correct else 0)
            mastery_level = new_correct_count / new_attempts
            db.execute("""UPDATE mastery_signals SET mastery_level = ?, attempts_count = ?, correct_count = ?, last_practiced = datetime('now')
                         WHERE student_id = ? AND skill_id = ?""",
                       (mastery_level, new_attempts, new_correct_count, student["id"], skill_id))
        else:
            db.execute("""INSERT INTO mastery_signals (student_id, skill_id, mastery_level, attempts_count, correct_count, last_practiced)
                         VALUES (?, ?, ?, 1, ?, datetime('now'))""",
                       (student["id"], skill_id, 1.0 if is_correct else 0.0, 1 if is_correct else 0))
        
        # Check if test is done (based on curriculum level question count)
        curriculum_level = get_student_curriculum_level(db, student["id"])
        total_placement_q = db.execute("""SELECT COUNT(*) as c FROM questions q
                                          JOIN skills sk ON q.skill_id = sk.id
                                          WHERE q.is_placement = 1 AND sk.curriculum_level = ?""",
                                       (curriculum_level,)).fetchone()["c"]
        answered_ids = [r["question_id"] for r in db.execute(
            "SELECT question_id FROM placement_answers WHERE placement_test_id = ?", (test["id"],)).fetchall()]
        
        is_complete = new_answered >= min(20, total_placement_q)
        
        if is_complete:
            score = (new_correct / new_answered) * 100 if new_answered > 0 else 0
            db.execute("""UPDATE placement_tests SET status = 'completed', completed_at = datetime('now')
                         WHERE id = ?""", (test["id"],))
            db.execute("UPDATE students SET placement_test_completed = 1, placement_test_score = ? WHERE id = ?",
                       (score, student["id"]))
            
            # Award achievement
            db.execute("INSERT INTO achievements (student_id, title, description, icon) VALUES (?, ?, ?, ?)",
                       (student["id"], "Explorador", "¡Completaste el placement test!", "🗺️"))
            
            return {
                "is_correct": is_correct,
                "correct_answer": question["correct_answer"],
                "explanation": question["explanation"],
                "test_complete": True,
                "score": round(score, 1),
                "questions_answered": new_answered,
                "correct_answers": new_correct
            }
        
        # Get next question
        next_q = get_next_placement_question(db, new_difficulty, answered_ids, student)
        
        return {
            "is_correct": is_correct,
            "correct_answer": question["correct_answer"],
            "explanation": question["explanation"],
            "hint": question["hint"] if not is_correct else None,
            "test_complete": False,
            "questions_answered": new_answered,
            "correct_answers": new_correct,
            "next_question": next_q
        }

@router.get("/placement-test/results")
async def get_placement_results(current_user: dict = Depends(require_roles("student"))):
    student = get_student(current_user)
    with get_db() as db:
        test = db.execute("SELECT * FROM placement_tests WHERE student_id = ? AND status = 'completed' ORDER BY completed_at DESC LIMIT 1",
                         (student["id"],)).fetchone()
        if not test:
            raise HTTPException(status_code=404, detail="No hay resultados del placement test")
        
        mastery = db.execute("""SELECT ms.*, sk.name, sk.category, sk.difficulty_level
                                FROM mastery_signals ms JOIN skills sk ON ms.skill_id = sk.id
                                WHERE ms.student_id = ? ORDER BY sk.order_index""",
                             (student["id"],)).fetchall()
        
        return {
            "test": dict(test),
            "mastery_map": [dict(m) for m in mastery]
        }

def get_student_curriculum_level(db, student_id):
    """Get curriculum level based on student's classroom"""
    row = db.execute("""SELECT g.level FROM students s
                        JOIN classrooms c ON s.classroom_id = c.id
                        JOIN grades g ON c.grade_id = g.id
                        WHERE s.id = ?""", (student_id,)).fetchone()
    if row and row["level"] == 0:
        return "kinder"
    return "4to_grado"

def get_next_placement_question(db, difficulty, answered_ids, student):
    """Get the next adaptive placement question"""
    interests = json.loads(student.get("interests", "[]") or "[]")
    curriculum_level = get_student_curriculum_level(db, student["id"])
    
    # Build exclusion
    exclude = ",".join(str(i) for i in answered_ids) if answered_ids else "0"
    
    # Try to find question matching difficulty, curriculum_level and interests
    query = f"""SELECT q.* FROM questions q
                JOIN skills sk ON q.skill_id = sk.id
                WHERE q.is_placement = 1 AND q.id NOT IN ({exclude})
                AND sk.curriculum_level = ? AND q.difficulty = ?
                ORDER BY RANDOM() LIMIT 1"""
    q = db.execute(query, (curriculum_level, difficulty)).fetchone()
    
    if not q:
        # Fallback: any unanswered placement question for this curriculum
        q = db.execute(f"""SELECT q.* FROM questions q
                           JOIN skills sk ON q.skill_id = sk.id
                           WHERE q.is_placement = 1 AND q.id NOT IN ({exclude})
                           AND sk.curriculum_level = ?
                           ORDER BY RANDOM() LIMIT 1""", (curriculum_level,)).fetchone()
    
    if not q:
        return None
    
    result = dict(q)
    # Remove answer-related fields to prevent cheating
    result.pop("correct_answer", None)
    result.pop("hint", None)
    result.pop("explanation", None)
    if result.get("options"):
        result["options"] = json.loads(result["options"])
    return result

# ---- Daily Mission ----
@router.get("/daily-mission")
async def get_daily_mission(current_user: dict = Depends(require_roles("student"))):
    student = get_student(current_user)
    with get_db() as db:
        # Check for existing today's session
        session = db.execute("""SELECT ds.*, sk.name as skill_name, sk.category
                                FROM daily_sessions ds LEFT JOIN skills sk ON ds.target_skill_id = sk.id
                                WHERE ds.student_id = ? AND ds.session_date = date('now')
                                ORDER BY ds.started_at DESC LIMIT 1""",
                             (student["id"],)).fetchone()
        
        if session:
            # Get questions for this session
            questions = get_session_questions(db, session["target_skill_id"], student)
            answered = db.execute("SELECT question_id FROM session_attempts WHERE session_id = ?", (session["id"],)).fetchall()
            answered_ids = [a["question_id"] for a in answered]
            
            return {
                "session": dict(session),
                "questions": questions,
                "answered_ids": answered_ids,
                "total_questions": len(questions)
            }
        
        # Create new daily mission - find the best skill to work on
        target_skill = find_next_skill(db, student["id"])
        if not target_skill:
            return {"session": None, "message": "¡Has completado todas las habilidades disponibles!"}
        
        skill = db.execute("SELECT * FROM skills WHERE id = ?", (target_skill,)).fetchone()
        mission_titles = [
            f"¡Hoy vas a dominar: {skill['name']}!",
            f"Misión del día: {skill['name']}",
            f"¡Vamos con {skill['name']}!",
            f"Tu reto de hoy: {skill['name']}"
        ]
        
        db.execute("""INSERT INTO daily_sessions (student_id, target_skill_id, mission_title, status)
                     VALUES (?, ?, ?, 'pending')""",
                   (student["id"], target_skill, random.choice(mission_titles)))
        session_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
        
        session = db.execute("""SELECT ds.*, sk.name as skill_name, sk.category
                                FROM daily_sessions ds LEFT JOIN skills sk ON ds.target_skill_id = sk.id
                                WHERE ds.id = ?""", (session_id,)).fetchone()
        
        questions = get_session_questions(db, target_skill, student)
        
        return {
            "session": dict(session),
            "questions": questions,
            "answered_ids": [],
            "total_questions": len(questions)
        }

@router.post("/exercise/answer")
async def answer_exercise(req: AnswerSubmit, current_user: dict = Depends(require_roles("student"))):
    student = get_student(current_user)
    with get_db() as db:
        # Get active session
        session = db.execute("""SELECT * FROM daily_sessions WHERE student_id = ? AND session_date = date('now')
                                AND status IN ('pending', 'in_progress') ORDER BY started_at DESC LIMIT 1""",
                             (student["id"],)).fetchone()
        if not session:
            raise HTTPException(status_code=400, detail="No hay sesión activa")
        
        # Mark session as in_progress if pending
        if session["status"] == "pending":
            db.execute("UPDATE daily_sessions SET status = 'in_progress' WHERE id = ?", (session["id"],))
        
        # Check answer
        question = db.execute("SELECT * FROM questions WHERE id = ?", (req.question_id,)).fetchone()
        if not question:
            raise HTTPException(status_code=404, detail="Pregunta no encontrada")
        
        is_correct = req.answer.strip().lower() == question["correct_answer"].strip().lower()
        
        # Count existing attempts for this question in this session
        attempt_count = db.execute("""SELECT COUNT(*) as c FROM session_attempts 
                                     WHERE session_id = ? AND question_id = ?""",
                                   (session["id"], req.question_id)).fetchone()["c"]
        
        # Save attempt
        db.execute("""INSERT INTO session_attempts (session_id, question_id, student_answer, is_correct, attempt_number, time_spent_seconds)
                     VALUES (?, ?, ?, ?, ?, ?)""",
                   (session["id"], req.question_id, req.answer, int(is_correct), attempt_count + 1, req.time_spent_seconds))
        
        # Update session counters
        total_q = db.execute("SELECT COUNT(DISTINCT question_id) as c FROM session_attempts WHERE session_id = ?",
                            (session["id"],)).fetchone()["c"]
        correct_q = db.execute("""SELECT COUNT(DISTINCT question_id) as c FROM session_attempts 
                                  WHERE session_id = ? AND is_correct = 1""",
                               (session["id"],)).fetchone()["c"]
        total_time = db.execute("SELECT COALESCE(SUM(time_spent_seconds), 0) as t FROM session_attempts WHERE session_id = ?",
                               (session["id"],)).fetchone()["t"]
        
        db.execute("""UPDATE daily_sessions SET total_questions = ?, correct_answers = ?, active_time_seconds = ?
                     WHERE id = ?""", (total_q, correct_q, total_time, session["id"]))
        
        # Update mastery + Elo ratings via Flow Engine
        skill_id = question["skill_id"]
        mastery_row = _load_or_create_mastery(db, student["id"], skill_id)
        
        theta_before = mastery_row["theta"] or CFG.INITIAL_THETA
        b_before = question["elo_b"] if question["elo_b"] is not None else CFG.INITIAL_B
        times_before = question["times_answered"] if question["times_answered"] is not None else 0
        
        # Elo update
        new_theta, new_b, expected_p = elo_update(
            theta=theta_before,
            elo_b=b_before,
            was_correct=is_correct,
            times_answered_before=times_before,
        )
        
        # Forgetting curve update
        new_hl = update_half_life(
            mastery_row["half_life_days"] or CFG.HALF_LIFE_INIT_DAYS, is_correct
        )
        new_strength = update_strength(is_correct)
        now_iso = datetime.now(timezone.utc).isoformat()
        
        # Update mastery row with Elo + forgetting data
        new_attempts = (mastery_row["attempts_count"] or 0) + 1
        new_correct_count = (mastery_row["correct_count"] or 0) + (1 if is_correct else 0)
        mastery_level = new_correct_count / max(1, new_attempts)
        
        db.execute("""UPDATE mastery_signals
                     SET mastery_level = ?, attempts_count = ?, correct_count = ?,
                         last_practiced = datetime('now'),
                         theta = ?, half_life_days = ?, strength = ?,
                         strength_updated_at = ?
                     WHERE student_id = ? AND skill_id = ?""",
                   (mastery_level, new_attempts, new_correct_count,
                    new_theta, new_hl, new_strength, now_iso,
                    student["id"], skill_id))
        
        # Update question Elo rating
        db.execute("""UPDATE questions
                     SET elo_b = ?,
                         times_answered = COALESCE(times_answered, 0) + 1,
                         times_correct = COALESCE(times_correct, 0) + ?
                     WHERE id = ?""",
                   (new_b, 1 if is_correct else 0, question["id"]))
        
        # Flow Engine telemetry
        db.execute("""INSERT INTO flow_events (
                        event_type, student_id, question_id, skill_id,
                        theta_at, elo_b_at, expected_p,
                        was_correct, time_taken_ms,
                        theta_delta, elo_b_delta, session_id
                     ) VALUES ('answer', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                   (student["id"], question["id"], skill_id,
                    theta_before, b_before, expected_p,
                    1 if is_correct else 0, req.time_spent_seconds * 1000,
                    new_theta - theta_before, new_b - b_before,
                    str(session["id"])))
        
        # Check if session is complete (8+ questions answered with >=90% accuracy)
        session_total = 8
        all_answered = total_q >= session_total
        accuracy = (correct_q / total_q * 100) if total_q > 0 else 0
        session_complete = all_answered and accuracy >= 90
        
        # --- Gamification: XP + Streak ---
        streak_days = student.get("streak_days") or 0
        streak_last = student.get("streak_last_date")
        new_streak, today_str = update_streak(streak_last, streak_days)
        
        # Award answer XP
        answer_xp = calculate_answer_xp(is_correct, new_streak)
        current_xp = (student.get("total_xp") or 0) + answer_xp
        new_level = xp_to_level(current_xp)
        old_level = student.get("level") or 1
        leveled_up = new_level > old_level
        
        # Update student gamification state
        longest = max(student.get("longest_streak") or 0, new_streak)
        db.execute(
            """UPDATE students SET total_xp = ?, level = ?, streak_days = ?, 
               streak_last_date = ?, longest_streak = ? WHERE id = ?""",
            (current_xp, new_level, new_streak, today_str, longest, student["id"])
        )
        
        if session_complete:
            db.execute("""UPDATE daily_sessions SET status = 'completed', completed_at = datetime('now')
                         WHERE id = ?""", (session["id"],))
            # Session completion XP
            session_xp_info = calculate_session_xp(correct_q, total_q, new_streak)
            current_xp += session_xp_info["total"]
            new_level = xp_to_level(current_xp)
            leveled_up = new_level > old_level
            db.execute("UPDATE students SET total_xp = ?, level = ? WHERE id = ?",
                       (current_xp, new_level, student["id"]))
        elif all_answered and accuracy < 90:
            # Need to retry some questions - don't complete yet
            pass
        
        # Check for new badges
        new_badges = check_badges(db, student["id"], current_xp, new_streak)
        
        response = {
            "is_correct": is_correct,
            "correct_answer": question["correct_answer"],
            "explanation": question["explanation"] if not is_correct else None,
            "hint": question["hint"] if not is_correct and attempt_count == 0 else None,
            "attempt_number": attempt_count + 1,
            "session_complete": session_complete,
            "accuracy": round(accuracy, 1),
            "questions_answered": total_q,
            "correct_answers": correct_q,
            "total_time_seconds": total_time,
            "xp_earned": answer_xp + (calculate_session_xp(correct_q, total_q, new_streak)["total"] if session_complete else 0),
            "total_xp": current_xp,
            "level": new_level,
            "leveled_up": leveled_up,
            "streak_days": new_streak,
            "new_badges": new_badges,
        }
        
        if session_complete:
            response["celebration"] = "🎉 ¡Excelente trabajo! ¡Misión completada!"
            response["session_xp"] = calculate_session_xp(correct_q, total_q, new_streak)
        
        return response

@router.post("/exercise/session/{session_id}/rate")
async def rate_session(session_id: int, req: SessionRating, current_user: dict = Depends(require_roles("student"))):
    student = get_student(current_user)
    with get_db() as db:
        session = db.execute("SELECT * FROM daily_sessions WHERE id = ? AND student_id = ?", (session_id, student["id"])).fetchone()
        if not session:
            raise HTTPException(status_code=404, detail="Sesión no encontrada")
        db.execute("UPDATE daily_sessions SET rating = ? WHERE id = ?", (req.rating, session_id))
        return {"message": "¡Gracias por tu opinión!"}

# ---- Progress & Achievements ----
@router.get("/progress")
async def get_progress(current_user: dict = Depends(require_roles("student"))):
    student = get_student(current_user)
    with get_db() as db:
        mastery = db.execute("""SELECT ms.*, sk.name, sk.category, sk.difficulty_level, sk.order_index
                                FROM mastery_signals ms JOIN skills sk ON ms.skill_id = sk.id
                                WHERE ms.student_id = ? ORDER BY sk.order_index""",
                             (student["id"],)).fetchall()
        
        sessions = db.execute("""SELECT ds.*, sk.name as skill_name
                                 FROM daily_sessions ds LEFT JOIN skills sk ON ds.target_skill_id = sk.id
                                 WHERE ds.student_id = ? ORDER BY ds.started_at DESC LIMIT 30""",
                              (student["id"],)).fetchall()
        
        total_sessions = db.execute("SELECT COUNT(*) as c FROM daily_sessions WHERE student_id = ?",
                                   (student["id"],)).fetchone()["c"]
        completed = db.execute("SELECT COUNT(*) as c FROM daily_sessions WHERE student_id = ? AND status = 'completed'",
                              (student["id"],)).fetchone()["c"]
        avg_accuracy = db.execute("""SELECT COALESCE(AVG(CASE WHEN total_questions > 0 THEN correct_answers * 100.0 / total_questions ELSE 0 END), 0) as avg
                                    FROM daily_sessions WHERE student_id = ? AND status = 'completed'""",
                                 (student["id"],)).fetchone()["avg"]
        
        return {
            "mastery": [dict(m) for m in mastery],
            "recent_sessions": [dict(s) for s in sessions],
            "stats": {
                "total_sessions": total_sessions,
                "completed_sessions": completed,
                "avg_accuracy": round(avg_accuracy, 1),
                "skills_mastered": sum(1 for m in mastery if m["mastery_level"] >= 0.9),
                "total_skills": db.execute("SELECT COUNT(*) as c FROM skills WHERE curriculum_level = ?", (get_student_curriculum_level(db, student["id"]),)).fetchone()["c"]
            }
        }

@router.get("/skill-map")
async def get_skill_map(current_user: dict = Depends(require_roles("student"))):
    student = get_student(current_user)
    with get_db() as db:
        curriculum_level = get_student_curriculum_level(db, student["id"])
        skills = db.execute("SELECT * FROM skills WHERE curriculum_level = ? ORDER BY order_index", (curriculum_level,)).fetchall()
        mastery = db.execute("SELECT * FROM mastery_signals WHERE student_id = ?", (student["id"],)).fetchall()
        mastery_dict = {m["skill_id"]: m["mastery_level"] for m in mastery}
        
        skill_map = []
        for s in skills:
            skill_map.append({
                **dict(s),
                "mastery_level": mastery_dict.get(s["id"], 0),
                "status": "mastered" if mastery_dict.get(s["id"], 0) >= 0.9 else 
                          "in_progress" if mastery_dict.get(s["id"], 0) > 0 else "locked"
            })
        return skill_map

@router.get("/achievements")
async def get_achievements(current_user: dict = Depends(require_roles("student"))):
    student = get_student(current_user)
    with get_db() as db:
        achievements_list = db.execute("SELECT * FROM achievements WHERE student_id = ? ORDER BY earned_at DESC",
                                (student["id"],)).fetchall()
        earned = [dict(a) for a in achievements_list]
        earned_ids = {a.get("badge_id") for a in earned if a.get("badge_id")}
        
        # Include available (unearned) badges
        available = []
        for b in BADGES:
            if b.id not in earned_ids:
                available.append({
                    "badge_id": b.id,
                    "title": b.title,
                    "description": b.description,
                    "icon": b.icon,
                    "category": b.category,
                    "locked": True,
                })
        
        return {
            "earned": earned,
            "available": available,
            "total_earned": len(earned),
            "total_available": len(BADGES),
        }


@router.get("/gamification")
async def get_gamification_stats(current_user: dict = Depends(require_roles("student"))):
    """Get full gamification state: XP, level, streak, badges."""
    student = get_student(current_user)
    with get_db() as db:
        # Refresh student data
        s = db.execute("SELECT * FROM students WHERE id = ?", (student["id"],)).fetchone()
        total_xp = s["total_xp"] or 0
        streak = s["streak_days"] or 0
        longest = s["longest_streak"] or 0
        
        lp = level_progress(total_xp)
        
        # Recent badges (last 5)
        recent_badges = db.execute(
            "SELECT * FROM achievements WHERE student_id = ? ORDER BY earned_at DESC LIMIT 5",
            (student["id"],)
        ).fetchall()
        
        # Stats
        completed_sessions = db.execute(
            "SELECT COUNT(*) as c FROM daily_sessions WHERE student_id = ? AND status = 'completed'",
            (student["id"],)
        ).fetchone()["c"]
        
        perfect_sessions = db.execute(
            """SELECT COUNT(*) as c FROM daily_sessions 
               WHERE student_id = ? AND status = 'completed' 
               AND total_questions > 0 AND correct_answers = total_questions""",
            (student["id"],)
        ).fetchone()["c"]
        
        return {
            **lp,
            "streak_days": streak,
            "longest_streak": longest,
            "completed_sessions": completed_sessions,
            "perfect_sessions": perfect_sessions,
            "recent_badges": [dict(b) for b in recent_badges],
        }

@router.post("/help-request")
async def request_help(current_user: dict = Depends(require_roles("student"))):
    student = get_student(current_user)
    with get_db() as db:
        session = db.execute("""SELECT * FROM daily_sessions WHERE student_id = ? AND session_date = date('now')
                                AND status IN ('pending', 'in_progress') ORDER BY started_at DESC LIMIT 1""",
                             (student["id"],)).fetchone()
        session_id = session["id"] if session else None
        db.execute("INSERT INTO help_requests (student_id, session_id) VALUES (?, ?)",
                   (student["id"], session_id))
        return {"message": "¡Tu coach ha sido notificado! Ya viene a ayudarte.", "icon": "🆘"}

def _load_or_create_mastery(db, student_id: int, skill_id: int) -> dict:
    """Load mastery row for (student, skill), creating one if it doesn't exist."""
    row = db.execute(
        "SELECT * FROM mastery_signals WHERE student_id = ? AND skill_id = ?",
        (student_id, skill_id),
    ).fetchone()
    if row:
        return dict(row)
    # First time for this (student, skill) — insert with Flow Engine defaults
    db.execute(
        """INSERT INTO mastery_signals (
              student_id, skill_id, mastery_level, attempts_count, correct_count,
              last_practiced, theta, half_life_days, strength, strength_updated_at
           ) VALUES (?, ?, 0.0, 0, 0, NULL, ?, ?, 1.0, NULL)""",
        (student_id, skill_id, CFG.INITIAL_THETA, CFG.HALF_LIFE_INIT_DAYS),
    )
    return dict(db.execute(
        "SELECT * FROM mastery_signals WHERE student_id = ? AND skill_id = ?",
        (student_id, skill_id),
    ).fetchone())


def find_next_skill(db, student_id):
    """Find the next skill the student should work on based on mastery and prerequisites"""
    curriculum_level = get_student_curriculum_level(db, student_id)
    skills = db.execute("SELECT * FROM skills WHERE curriculum_level = ? ORDER BY order_index", (curriculum_level,)).fetchall()
    mastery = db.execute("SELECT skill_id, mastery_level FROM mastery_signals WHERE student_id = ?",
                        (student_id,)).fetchall()
    mastery_dict = {m["skill_id"]: m["mastery_level"] for m in mastery}
    
    for skill in skills:
        current_mastery = mastery_dict.get(skill["id"], 0)
        if current_mastery >= 0.9:
            continue  # Already mastered
        
        # Check prerequisite
        if skill["prerequisite_skill_id"]:
            prereq_mastery = mastery_dict.get(skill["prerequisite_skill_id"], 0)
            if prereq_mastery < 0.8:
                continue  # Prerequisite not met
        
        return skill["id"]
    
    # If all mastered or no valid next, return first non-mastered
    for skill in skills:
        if mastery_dict.get(skill["id"], 0) < 0.9:
            return skill["id"]
    
    return None

def get_session_questions(db, skill_id, student):
    """Get questions for a daily session using Flow Engine selector + spaced repetition."""
    interests = json.loads(student.get("interests", "[]") or "[]")
    
    # Load or create mastery for the target skill
    mastery_row = _load_or_create_mastery(db, student["id"], skill_id)
    theta = mastery_row["theta"] or CFG.INITIAL_THETA
    streak = StreakState()
    session_id_str = f"mission-{student['id']}-{skill_id}"
    
    # Main skill questions (8) via Flow Engine selector
    main_qs = []
    seen_ids = set()
    for _ in range(12):  # try up to 12 times to get 8 unique questions
        if len(main_qs) >= 8:
            break
        q = select_next_question(
            conn=db,
            student_id=student["id"],
            skill_id=skill_id,
            theta=theta,
            streak=streak,
            interest_tags=interests,
            session_id=session_id_str,
            exclude_ids=seen_ids,
        )
        if q and q["id"] not in seen_ids:
            main_qs.append(q)
            seen_ids.add(q["id"])
    
    # If not enough from Flow Engine, fall back to random selection
    if len(main_qs) < 5:
        fallback_qs = db.execute("""SELECT * FROM questions WHERE skill_id = ? AND is_placement = 0
                                    AND id NOT IN ({})
                                    ORDER BY RANDOM() LIMIT ?""".format(
                                    ",".join(str(i) for i in seen_ids) if seen_ids else "0"),
                                (skill_id, 8 - len(main_qs))).fetchall()
        for q in fallback_qs:
            qd = dict(q)
            if qd["id"] not in seen_ids:
                main_qs.append(qd)
                seen_ids.add(qd["id"])
        # Also try placement questions as last resort
        if len(main_qs) < 5:
            extra = db.execute("""SELECT * FROM questions WHERE skill_id = ? AND is_placement = 1
                                  AND id NOT IN ({})
                                  ORDER BY RANDOM() LIMIT ?""".format(
                                  ",".join(str(i) for i in seen_ids) if seen_ids else "0"),
                              (skill_id, 5 - len(main_qs))).fetchall()
            for q in extra:
                main_qs.append(dict(q))
    
    # Spaced repetition: 3 review questions from decaying skills
    review_qs = []
    review_rows = db.execute(
        """SELECT skill_id, theta, half_life_days, strength, last_practiced
             FROM mastery_signals
            WHERE student_id = ? AND mastery_level >= 0.5 AND skill_id != ?""",
        (student["id"], skill_id),
    ).fetchall()
    
    review_candidates = []
    for r in review_rows:
        last_practiced = None
        if r["last_practiced"]:
            try:
                last_practiced = datetime.fromisoformat(str(r["last_practiced"]).replace("Z", "+00:00"))
            except (ValueError, TypeError):
                pass
        s = decayed_strength(
            r["strength"] or 1.0,
            r["half_life_days"] or CFG.HALF_LIFE_INIT_DAYS,
            last_practiced,
        )
        if s < CFG.STRENGTH_REVIEW_THRESHOLD:
            review_candidates.append((s, dict(r)))
    review_candidates.sort(key=lambda x: x[0])  # weakest first
    
    for _, r in review_candidates[:3]:
        review_theta = r["theta"] or CFG.INITIAL_THETA
        q = select_next_question(
            conn=db,
            student_id=student["id"],
            skill_id=r["skill_id"],
            theta=review_theta,
            streak=StreakState(),
            interest_tags=interests,
            session_id=session_id_str,
            exclude_ids=seen_ids,
        )
        if q and q["id"] not in seen_ids:
            review_qs.append(q)
            seen_ids.add(q["id"])
    
    all_qs = main_qs + review_qs
    result = []
    for q in all_qs:
        qd = q if isinstance(q, dict) else dict(q)
        if qd.get("options") and isinstance(qd["options"], str):
            qd["options"] = json.loads(qd["options"])
        # Remove internal Flow Engine fields and answer data from response
        qd.pop("_expected_p", None)
        qd.pop("_fallback", None)
        qd.pop("correct_answer", None)
        qd.pop("hint", None)
        qd.pop("explanation", None)
        result.append(qd)
    
    random.shuffle(result)
    return result
