-- migrations/001_elo_flow_engine.sql
-- Additive migration for Thriveed Flow Engine (Elo-based adaptive difficulty)
-- Safe to re-run (uses IF NOT EXISTS / conditional updates)

-- Per-question Elo rating and attempt counter
ALTER TABLE questions ADD COLUMN elo_b REAL DEFAULT 1000.0;
ALTER TABLE questions ADD COLUMN times_answered INTEGER DEFAULT 0;
ALTER TABLE questions ADD COLUMN times_correct INTEGER DEFAULT 0;
ALTER TABLE questions ADD COLUMN needs_review INTEGER DEFAULT 0;

-- Per-(student,skill) ability + forgetting state
ALTER TABLE mastery_signals ADD COLUMN theta REAL DEFAULT 1000.0;
ALTER TABLE mastery_signals ADD COLUMN half_life_days REAL DEFAULT 1.0;
ALTER TABLE mastery_signals ADD COLUMN strength REAL DEFAULT 1.0;
ALTER TABLE mastery_signals ADD COLUMN strength_updated_at TIMESTAMP;

-- Append-only telemetry
CREATE TABLE IF NOT EXISTS flow_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  event_type TEXT NOT NULL,        -- 'serve' | 'answer'
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
CREATE INDEX IF NOT EXISTS idx_questions_skill_elo ON questions(skill_id, elo_b);

-- Backfill elo_b from legacy difficulty
UPDATE questions
   SET elo_b = 800 + (COALESCE(difficulty, 2) * 100)
 WHERE elo_b = 1000.0;
