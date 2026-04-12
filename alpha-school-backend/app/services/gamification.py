"""
ThriveEd Gamification Service
------------------------------
XP calculation, level system, badge definitions, and streak tracking.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
from datetime import date

# ---------- XP & Level System ------------------------------------------------

# XP rewards per action
XP_CORRECT_ANSWER = 10
XP_WRONG_ANSWER = 2  # participation XP
XP_SESSION_COMPLETE = 50
XP_PERFECT_SESSION = 100  # bonus for 100% accuracy
XP_STREAK_BONUS_PER_DAY = 5  # multiplied by streak length (capped at 7)

# Level thresholds: level N requires LEVEL_THRESHOLDS[N-1] total XP
LEVEL_THRESHOLDS = [
    0,      # Level 1: 0 XP
    100,    # Level 2: 100 XP
    300,    # Level 3: 300 XP
    600,    # Level 4: 600 XP
    1000,   # Level 5: 1000 XP
    1500,   # Level 6: 1500 XP
    2200,   # Level 7: 2200 XP
    3000,   # Level 8: 3000 XP
    4000,   # Level 9: 4000 XP
    5200,   # Level 10: 5200 XP
    6500,   # Level 11
    8000,   # Level 12
    10000,  # Level 13
    12500,  # Level 14
    15500,  # Level 15
]

LEVEL_TITLES = [
    "Explorador",        # 1
    "Aprendiz",          # 2
    "Estudiante",        # 3
    "Practicante",       # 4
    "Conocedor",         # 5
    "Habilidoso",        # 6
    "Experto",           # 7
    "Maestro",           # 8
    "Sabio",             # 9
    "Genio",             # 10
    "Leyenda",           # 11
    "Titán",             # 12
    "Campeón",           # 13
    "Héroe",             # 14
    "Leyenda Suprema",   # 15
]

LEVEL_ICONS = [
    "🌱", "🌿", "🌳", "⭐", "🌟",
    "💫", "🔥", "👑", "🧠", "🏆",
    "💎", "⚡", "🦅", "🐉", "🌈",
]


def xp_to_level(total_xp: int) -> int:
    """Calculate level from total XP."""
    level = 1
    for i, threshold in enumerate(LEVEL_THRESHOLDS):
        if total_xp >= threshold:
            level = i + 1
        else:
            break
    return min(level, len(LEVEL_THRESHOLDS))


def level_progress(total_xp: int) -> dict:
    """Get level progress details."""
    level = xp_to_level(total_xp)
    current_threshold = LEVEL_THRESHOLDS[level - 1] if level - 1 < len(LEVEL_THRESHOLDS) else LEVEL_THRESHOLDS[-1]
    next_threshold = LEVEL_THRESHOLDS[level] if level < len(LEVEL_THRESHOLDS) else current_threshold + 2000

    xp_in_level = total_xp - current_threshold
    xp_needed = next_threshold - current_threshold
    progress_pct = min(100.0, (xp_in_level / max(1, xp_needed)) * 100)

    title_idx = min(level - 1, len(LEVEL_TITLES) - 1)
    icon_idx = min(level - 1, len(LEVEL_ICONS) - 1)

    return {
        "level": level,
        "title": LEVEL_TITLES[title_idx],
        "icon": LEVEL_ICONS[icon_idx],
        "total_xp": total_xp,
        "xp_in_level": xp_in_level,
        "xp_for_next": xp_needed,
        "progress_percent": round(progress_pct, 1),
        "next_level_xp": next_threshold,
    }


def calculate_answer_xp(is_correct: bool, streak_days: int) -> int:
    """Calculate XP earned for a single answer."""
    base = XP_CORRECT_ANSWER if is_correct else XP_WRONG_ANSWER
    streak_bonus = min(streak_days, 7) * XP_STREAK_BONUS_PER_DAY if is_correct else 0
    return base + streak_bonus


def calculate_session_xp(correct: int, total: int, streak_days: int) -> dict:
    """Calculate total XP for completing a session."""
    base = XP_SESSION_COMPLETE
    accuracy = correct / max(1, total)
    perfect_bonus = XP_PERFECT_SESSION if accuracy >= 1.0 else 0
    streak_bonus = min(streak_days, 7) * XP_STREAK_BONUS_PER_DAY

    return {
        "base": base,
        "perfect_bonus": perfect_bonus,
        "streak_bonus": streak_bonus,
        "total": base + perfect_bonus + streak_bonus,
    }


# ---------- Streak System ---------------------------------------------------

def update_streak(last_streak_date: Optional[str], current_streak: int) -> tuple[int, str]:
    """
    Update streak based on today's date.
    Returns (new_streak_days, today_str).
    """
    today = date.today().isoformat()
    if not last_streak_date:
        return 1, today

    from datetime import timedelta
    last = date.fromisoformat(last_streak_date)
    diff = (date.today() - last).days

    if diff == 0:
        # Already played today
        return current_streak, today
    elif diff == 1:
        # Consecutive day
        return current_streak + 1, today
    else:
        # Streak broken
        return 1, today


# ---------- Badge/Achievement Definitions -----------------------------------

@dataclass
class BadgeDefinition:
    id: str
    title: str
    description: str
    icon: str
    category: str  # "streak", "mastery", "session", "special"
    condition_desc: str


BADGES = [
    # Streak badges
    BadgeDefinition("streak_3", "Racha de 3", "¡3 días seguidos!", "🔥", "streak", "3 day streak"),
    BadgeDefinition("streak_7", "Semana Completa", "¡7 días seguidos!", "🔥🔥", "streak", "7 day streak"),
    BadgeDefinition("streak_14", "Dos Semanas", "¡14 días seguidos!", "🔥🔥🔥", "streak", "14 day streak"),
    BadgeDefinition("streak_30", "Mes Completo", "¡30 días seguidos!", "💎", "streak", "30 day streak"),

    # Session badges
    BadgeDefinition("first_session", "Primera Misión", "¡Completaste tu primera sesión!", "🎯", "session", "Complete first session"),
    BadgeDefinition("sessions_10", "Veterano", "¡10 sesiones completadas!", "🏅", "session", "Complete 10 sessions"),
    BadgeDefinition("sessions_50", "Dedicado", "¡50 sesiones completadas!", "🥇", "session", "Complete 50 sessions"),
    BadgeDefinition("perfect_session", "Perfección", "¡Sesión perfecta!", "💯", "session", "100% accuracy in a session"),
    BadgeDefinition("perfect_5", "Maestro Perfecto", "¡5 sesiones perfectas!", "👑", "session", "5 perfect sessions"),

    # Mastery badges
    BadgeDefinition("skill_master_1", "Primer Dominio", "¡Dominaste tu primer skill!", "⭐", "mastery", "Master first skill"),
    BadgeDefinition("skill_master_5", "Multi-Talento", "¡5 skills dominados!", "🌟", "mastery", "Master 5 skills"),
    BadgeDefinition("skill_master_10", "Experto", "¡10 skills dominados!", "💫", "mastery", "Master 10 skills"),
    BadgeDefinition("all_skills", "Legendario", "¡Todos los skills dominados!", "🏆", "mastery", "Master all skills"),

    # XP/Level badges
    BadgeDefinition("level_5", "Nivel 5", "¡Llegaste al nivel 5!", "🌟", "special", "Reach level 5"),
    BadgeDefinition("level_10", "Nivel 10", "¡Llegaste al nivel 10!", "🏆", "special", "Reach level 10"),
    BadgeDefinition("xp_1000", "Mil Puntos", "¡1000 XP acumulados!", "💰", "special", "Earn 1000 XP"),
    BadgeDefinition("xp_5000", "Rico en XP", "¡5000 XP acumulados!", "💎", "special", "Earn 5000 XP"),

    # Special
    BadgeDefinition("speed_demon", "Rayo", "¡5 respuestas correctas en <10s!", "⚡", "special", "5 fast correct answers"),
    BadgeDefinition("comeback", "Comeback", "¡3 correctas después de 3 incorrectas!", "💪", "special", "3 correct after 3 wrong"),
]

BADGE_MAP = {b.id: b for b in BADGES}


def check_badges(db, student_id: int, total_xp: int, streak_days: int) -> list[dict]:
    """
    Check which badges the student has earned but not yet received.
    Returns list of newly earned badge dicts.
    """
    # Get existing achievement badge_ids
    existing = db.execute(
        "SELECT badge_id FROM achievements WHERE student_id = ? AND badge_id IS NOT NULL",
        (student_id,)
    ).fetchall()
    existing_ids = {r["badge_id"] for r in existing}

    # Get stats
    completed_sessions = db.execute(
        "SELECT COUNT(*) as c FROM daily_sessions WHERE student_id = ? AND status = 'completed'",
        (student_id,)
    ).fetchone()["c"]

    perfect_sessions = db.execute(
        """SELECT COUNT(*) as c FROM daily_sessions 
           WHERE student_id = ? AND status = 'completed' 
           AND total_questions > 0 AND correct_answers = total_questions""",
        (student_id,)
    ).fetchone()["c"]

    mastered_skills = db.execute(
        "SELECT COUNT(*) as c FROM mastery_signals WHERE student_id = ? AND mastery_level >= 0.9",
        (student_id,)
    ).fetchone()["c"]

    level = xp_to_level(total_xp)

    newly_earned = []

    def try_award(badge_id: str, condition: bool):
        if condition and badge_id not in existing_ids:
            badge = BADGE_MAP.get(badge_id)
            if badge:
                db.execute(
                    """INSERT INTO achievements (student_id, title, description, icon, badge_id, category)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (student_id, badge.title, badge.description, badge.icon, badge.id, badge.category)
                )
                newly_earned.append({
                    "badge_id": badge.id,
                    "title": badge.title,
                    "description": badge.description,
                    "icon": badge.icon,
                    "category": badge.category,
                })

    # Streak badges
    try_award("streak_3", streak_days >= 3)
    try_award("streak_7", streak_days >= 7)
    try_award("streak_14", streak_days >= 14)
    try_award("streak_30", streak_days >= 30)

    # Session badges
    try_award("first_session", completed_sessions >= 1)
    try_award("sessions_10", completed_sessions >= 10)
    try_award("sessions_50", completed_sessions >= 50)
    try_award("perfect_session", perfect_sessions >= 1)
    try_award("perfect_5", perfect_sessions >= 5)

    # Mastery badges
    try_award("skill_master_1", mastered_skills >= 1)
    try_award("skill_master_5", mastered_skills >= 5)
    try_award("skill_master_10", mastered_skills >= 10)

    # Level/XP badges
    try_award("level_5", level >= 5)
    try_award("level_10", level >= 10)
    try_award("xp_1000", total_xp >= 1000)
    try_award("xp_5000", total_xp >= 5000)

    return newly_earned
