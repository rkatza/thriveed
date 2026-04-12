import sqlite3
import os
from contextlib import contextmanager

DB_PATH = os.environ.get("DATABASE_PATH", "/data/app.db") if os.path.exists("/data") else os.environ.get("DATABASE_PATH", "app.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

@contextmanager
def get_db():
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    with get_db() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS schools (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            address TEXT,
            city TEXT DEFAULT 'Panamá',
            phone TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS grades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            school_id INTEGER NOT NULL REFERENCES schools(id),
            name TEXT NOT NULL,
            level INTEGER NOT NULL DEFAULT 4,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS classrooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            grade_id INTEGER NOT NULL REFERENCES grades(id),
            name TEXT NOT NULL,
            group_type TEXT DEFAULT 'treatment' CHECK(group_type IN ('treatment', 'control')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('super_admin', 'admin', 'coach', 'parent', 'student')),
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL REFERENCES users(id),
            classroom_id INTEGER REFERENCES classrooms(id),
            nickname TEXT,
            avatar_url TEXT DEFAULT '🧒',
            age INTEGER DEFAULT 9,
            interests TEXT DEFAULT '[]',
            placement_test_completed INTEGER DEFAULT 0,
            placement_test_score REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS coaches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL REFERENCES users(id),
            classroom_id INTEGER REFERENCES classrooms(id),
            specialization TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS parents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL REFERENCES users(id),
            phone TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS parent_students (
            parent_id INTEGER NOT NULL REFERENCES parents(id),
            student_id INTEGER NOT NULL REFERENCES students(id),
            PRIMARY KEY (parent_id, student_id)
        );

        CREATE TABLE IF NOT EXISTS skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            category TEXT NOT NULL,
            difficulty_level INTEGER DEFAULT 1,
            prerequisite_skill_id INTEGER REFERENCES skills(id),
            order_index INTEGER DEFAULT 0,
            curriculum_level TEXT DEFAULT '4to_grado',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS lessons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            skill_id INTEGER NOT NULL REFERENCES skills(id),
            title TEXT NOT NULL,
            description TEXT,
            content_type TEXT DEFAULT 'exercise',
            difficulty INTEGER DEFAULT 1,
            estimated_minutes INTEGER DEFAULT 5,
            is_published INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lesson_id INTEGER REFERENCES lessons(id),
            skill_id INTEGER NOT NULL REFERENCES skills(id),
            question_text TEXT NOT NULL,
            question_type TEXT DEFAULT 'multiple_choice' CHECK(question_type IN ('multiple_choice', 'numeric', 'true_false')),
            options TEXT,
            correct_answer TEXT NOT NULL,
            hint TEXT,
            explanation TEXT,
            difficulty INTEGER DEFAULT 1,
            is_placement INTEGER DEFAULT 0,
            interest_tags TEXT DEFAULT '[]',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS placement_tests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL REFERENCES students(id),
            status TEXT DEFAULT 'in_progress' CHECK(status IN ('in_progress', 'completed')),
            current_difficulty INTEGER DEFAULT 1,
            questions_answered INTEGER DEFAULT 0,
            correct_answers INTEGER DEFAULT 0,
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS placement_answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            placement_test_id INTEGER NOT NULL REFERENCES placement_tests(id),
            question_id INTEGER NOT NULL REFERENCES questions(id),
            student_answer TEXT,
            is_correct INTEGER,
            time_spent_seconds INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS mastery_signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL REFERENCES students(id),
            skill_id INTEGER NOT NULL REFERENCES skills(id),
            mastery_level REAL DEFAULT 0.0,
            attempts_count INTEGER DEFAULT 0,
            correct_count INTEGER DEFAULT 0,
            last_practiced TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(student_id, skill_id)
        );

        CREATE TABLE IF NOT EXISTS daily_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL REFERENCES students(id),
            target_skill_id INTEGER REFERENCES skills(id),
            mission_title TEXT,
            status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'in_progress', 'completed', 'paused')),
            total_questions INTEGER DEFAULT 0,
            correct_answers INTEGER DEFAULT 0,
            active_time_seconds INTEGER DEFAULT 0,
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            session_date DATE DEFAULT (date('now')),
            rating INTEGER
        );

        CREATE TABLE IF NOT EXISTS session_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL REFERENCES daily_sessions(id),
            question_id INTEGER NOT NULL REFERENCES questions(id),
            student_answer TEXT,
            is_correct INTEGER,
            attempt_number INTEGER DEFAULT 1,
            hint_used INTEGER DEFAULT 0,
            time_spent_seconds INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS interventions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            coach_id INTEGER NOT NULL REFERENCES coaches(id),
            student_id INTEGER NOT NULL REFERENCES students(id),
            session_id INTEGER REFERENCES daily_sessions(id),
            tag TEXT CHECK(tag IN ('frustration', 'conceptual_doubt', 'distraction', 'personal', 'other')),
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id INTEGER NOT NULL REFERENCES users(id),
            receiver_id INTEGER NOT NULL REFERENCES users(id),
            student_id INTEGER REFERENCES students(id),
            subject TEXT,
            body TEXT NOT NULL,
            is_read INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS help_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL REFERENCES students(id),
            session_id INTEGER REFERENCES daily_sessions(id),
            status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'attended', 'dismissed')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS achievements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL REFERENCES students(id),
            title TEXT NOT NULL,
            description TEXT,
            icon TEXT DEFAULT '⭐',
            badge_id TEXT,
            category TEXT DEFAULT 'special',
            earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES users(id),
            action TEXT NOT NULL,
            entity_type TEXT,
            entity_id INTEGER,
            details TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS invitations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('admin', 'coach', 'parent', 'student')),
            first_name TEXT,
            last_name TEXT,
            status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'accepted', 'revoked', 'expired')),
            invited_by INTEGER REFERENCES users(id),
            token TEXT UNIQUE,
            curriculum_level TEXT DEFAULT '4to_grado',
            classroom_id INTEGER REFERENCES classrooms(id),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            accepted_at TIMESTAMP
        );

        -- Flow Engine: append-only telemetry table
        CREATE TABLE IF NOT EXISTS flow_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            event_type TEXT NOT NULL,
            student_id INTEGER NOT NULL,
            question_id INTEGER NOT NULL,
            skill_id INTEGER NOT NULL,
            theta_at REAL,
            elo_b_at REAL,
            expected_p REAL,
            was_correct INTEGER,
            time_taken_ms INTEGER,
            theta_delta REAL,
            elo_b_delta REAL,
            interest_match INTEGER,
            selector_fallback INTEGER,
            session_id TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_flow_events_student ON flow_events(student_id, ts);
        CREATE INDEX IF NOT EXISTS idx_flow_events_session ON flow_events(student_id, session_id, event_type);
        """)

        # Flow Engine: additive ALTER TABLE migrations (safe to re-run)
        _run_flow_engine_migrations(db)
        # Gamification: additive ALTER TABLE migrations
        _run_gamification_migrations(db)


def _run_gamification_migrations(db):
    """Add gamification columns to existing tables. Safe to call multiple times."""
    student_cols = {row[1] for row in db.execute("PRAGMA table_info(students)").fetchall()}
    achievement_cols = {row[1] for row in db.execute("PRAGMA table_info(achievements)").fetchall()}

    # Gamification columns on students
    if "total_xp" not in student_cols:
        db.execute("ALTER TABLE students ADD COLUMN total_xp INTEGER DEFAULT 0")
    if "level" not in student_cols:
        db.execute("ALTER TABLE students ADD COLUMN level INTEGER DEFAULT 1")
    if "streak_days" not in student_cols:
        db.execute("ALTER TABLE students ADD COLUMN streak_days INTEGER DEFAULT 0")
    if "streak_last_date" not in student_cols:
        db.execute("ALTER TABLE students ADD COLUMN streak_last_date TEXT")
    if "longest_streak" not in student_cols:
        db.execute("ALTER TABLE students ADD COLUMN longest_streak INTEGER DEFAULT 0")

    # Badge tracking columns on achievements
    if "badge_id" not in achievement_cols:
        db.execute("ALTER TABLE achievements ADD COLUMN badge_id TEXT")
    if "category" not in achievement_cols:
        db.execute("ALTER TABLE achievements ADD COLUMN category TEXT DEFAULT 'special'")


def _run_flow_engine_migrations(db):
    """Add Flow Engine columns to existing tables. Safe to call multiple times."""
    # Check which columns already exist
    question_cols = {row[1] for row in db.execute("PRAGMA table_info(questions)").fetchall()}
    mastery_cols = {row[1] for row in db.execute("PRAGMA table_info(mastery_signals)").fetchall()}

    # Per-question Elo rating columns
    if "elo_b" not in question_cols:
        db.execute("ALTER TABLE questions ADD COLUMN elo_b REAL DEFAULT 1000.0")
    if "times_answered" not in question_cols:
        db.execute("ALTER TABLE questions ADD COLUMN times_answered INTEGER DEFAULT 0")
    if "times_correct" not in question_cols:
        db.execute("ALTER TABLE questions ADD COLUMN times_correct INTEGER DEFAULT 0")
    if "needs_review" not in question_cols:
        db.execute("ALTER TABLE questions ADD COLUMN needs_review INTEGER DEFAULT 0")

    # Per-(student,skill) ability + forgetting state
    if "theta" not in mastery_cols:
        db.execute("ALTER TABLE mastery_signals ADD COLUMN theta REAL DEFAULT 1000.0")
    if "half_life_days" not in mastery_cols:
        db.execute("ALTER TABLE mastery_signals ADD COLUMN half_life_days REAL DEFAULT 1.0")
    if "strength" not in mastery_cols:
        db.execute("ALTER TABLE mastery_signals ADD COLUMN strength REAL DEFAULT 1.0")
    if "strength_updated_at" not in mastery_cols:
        db.execute("ALTER TABLE mastery_signals ADD COLUMN strength_updated_at TIMESTAMP")

    # Index on elo_b (must run after column is added)
    db.execute("CREATE INDEX IF NOT EXISTS idx_questions_skill_elo ON questions(skill_id, elo_b)")

    # Backfill elo_b from legacy difficulty
    db.execute("""
        UPDATE questions
           SET elo_b = 800 + (COALESCE(difficulty, 2) * 100)
         WHERE elo_b = 1000.0 OR elo_b IS NULL
    """)
