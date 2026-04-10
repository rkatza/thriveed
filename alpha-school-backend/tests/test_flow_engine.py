import math
import sqlite3
import pytest
from datetime import datetime, timedelta, timezone

from app.services.flow_engine import (
    CFG,
    StreakState,
    apply_answer_to_streak,
    current_flow_band,
    decayed_strength,
    elo_update,
    expected_p_correct,
    question_k_factor,
    update_half_life,
    update_strength,
)
from app.services.question_selector import (
    _band_to_elo_range,
    select_next_question,
)

# ---- Unit tests ---------------------------------------------------------

def test_expected_p_symmetry():
    assert abs(expected_p_correct(1000, 1000) - 0.5) < 1e-9

def test_expected_p_monotonic():
    assert expected_p_correct(1200, 1000) > expected_p_correct(1000, 1000)
    assert expected_p_correct(800, 1000) < expected_p_correct(1000, 1000)

def test_elo_update_correct_answer_raises_theta():
    new_theta, new_b, _ = elo_update(1000, 1000, True, 10)
    assert new_theta > 1000
    assert new_b < 1000

def test_elo_update_incorrect_lowers_theta():
    new_theta, new_b, _ = elo_update(1000, 1000, False, 10)
    assert new_theta < 1000
    assert new_b > 1000

def test_elo_update_harder_question_gives_more_theta():
    """Answering a harder question correctly should give more theta gain."""
    theta_easy, _, _ = elo_update(1000, 800, True, 10)
    theta_hard, _, _ = elo_update(1000, 1200, True, 10)
    assert theta_hard - 1000 > theta_easy - 1000

def test_k_factor_damps_with_attempts():
    assert question_k_factor(0) > question_k_factor(500)
    assert question_k_factor(10_000) >= 2.0

def test_half_life_on_correct_grows():
    assert update_half_life(2.0, True) > 2.0

def test_half_life_on_wrong_shrinks():
    assert update_half_life(4.0, False) < 4.0

def test_half_life_cap():
    assert update_half_life(100.0, True) <= CFG.HALF_LIFE_CAP_DAYS

def test_half_life_floor():
    assert update_half_life(0.5, False) >= 0.5

def test_decay_drops_over_time():
    now = datetime.now(timezone.utc)
    long_ago = now - timedelta(days=30)
    assert decayed_strength(1.0, 3.0, long_ago, now) < 0.01

def test_decay_recent_stays_high():
    now = datetime.now(timezone.utc)
    recent = now - timedelta(hours=1)
    assert decayed_strength(1.0, 3.0, recent, now) > 0.95

def test_decay_none_last_practiced():
    assert decayed_strength(1.0, 3.0, None) == 1.0

def test_strength_correct():
    assert update_strength(True) == 1.0

def test_strength_wrong():
    assert update_strength(False) == 0.5

def test_rescue_band_after_two_wrong():
    streak = StreakState()
    apply_answer_to_streak(streak, False, 5000)
    apply_answer_to_streak(streak, False, 5000)
    p_min, p_max = current_flow_band(streak)
    assert p_min >= CFG.P_MIN_RESCUE

def test_stretch_band_after_three_fast_right():
    streak = StreakState()
    for _ in range(3):
        apply_answer_to_streak(streak, True, 4000)
    p_min, p_max = current_flow_band(streak)
    assert p_max <= CFG.P_MAX_STRETCH

def test_normal_band():
    streak = StreakState()
    p_min, p_max = current_flow_band(streak)
    assert p_min == CFG.P_MIN
    assert p_max == CFG.P_MAX

def test_streak_resets_on_opposite():
    streak = StreakState()
    apply_answer_to_streak(streak, False, 5000)
    apply_answer_to_streak(streak, False, 5000)
    assert streak.wrong_in_row == 2
    apply_answer_to_streak(streak, True, 5000)
    assert streak.wrong_in_row == 0
    assert streak.right_in_row == 1

def test_band_to_elo_range_inverts_expected_p():
    theta = 1100
    lo, hi = _band_to_elo_range(theta, 0.70, 0.80)
    # At b=lo we should see P ~ 0.80, at b=hi we should see P ~ 0.70
    assert abs(expected_p_correct(theta, lo) - 0.80) < 0.01
    assert abs(expected_p_correct(theta, hi) - 0.70) < 0.01

def test_theta_monotonic_on_correct_streak():
    """10 correct answers in a row should produce monotonically non-decreasing theta."""
    theta = CFG.INITIAL_THETA
    for i in range(10):
        new_theta, _, _ = elo_update(theta, 1000, True, i)
        assert new_theta >= theta
        theta = new_theta

# ---- Simulation --------------------------------------------------------

def _mem_db():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript("""
        CREATE TABLE questions (
            id INTEGER PRIMARY KEY,
            skill_id INTEGER, question_text TEXT, question_type TEXT,
            options TEXT, correct_answer TEXT, hint TEXT, explanation TEXT,
            difficulty INTEGER, is_placement INTEGER DEFAULT 0,
            interest_tags TEXT,
            elo_b REAL DEFAULT 1000.0,
            times_answered INTEGER DEFAULT 0,
            times_correct INTEGER DEFAULT 0,
            needs_review INTEGER DEFAULT 0
        );
        CREATE TABLE flow_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            event_type TEXT, student_id INTEGER, question_id INTEGER,
            skill_id INTEGER, theta_at REAL, elo_b_at REAL,
            expected_p REAL, was_correct INTEGER, time_taken_ms INTEGER,
            theta_delta REAL, elo_b_delta REAL,
            interest_match INTEGER, selector_fallback INTEGER,
            session_id TEXT
        );
    """)
    return conn

def _seed_questions(conn, n=60, skill_id=1):
    # Spread elo_b from 600 to 1400
    for i in range(n):
        b = 600 + (800 * i / (n - 1))
        conn.execute(
            """INSERT INTO questions
                 (id, skill_id, question_text, question_type, options,
                  correct_answer, elo_b)
               VALUES (?, ?, 'q', 'mc', '[]', 'A', ?)""",
            (i + 1, skill_id, b),
        )
    conn.commit()

def _simulated_student(true_theta: float):
    """Return a function that answers with P determined by true ability."""
    def answer(elo_b):
        p = expected_p_correct(true_theta, elo_b)
        import random as _rand
        return _rand.random() < p
    return answer

def test_simulation_converges_to_true_theta():
    import random
    random.seed(42)
    conn = _mem_db()
    _seed_questions(conn, n=80)

    true_theta = 1150
    student_answer = _simulated_student(true_theta)

    estimated_theta = CFG.INITIAL_THETA
    streak = StreakState()

    for _ in range(120):
        q = select_next_question(conn, student_id=1, skill_id=1,
                                 theta=estimated_theta, streak=streak)
        assert q is not None
        correct = student_answer(q["elo_b"])
        estimated_theta, new_b, _ = elo_update(
            estimated_theta, q["elo_b"], correct,
            q.get("times_answered") or 0,
        )
        conn.execute(
            "UPDATE questions SET elo_b = ?, times_answered = times_answered + 1 WHERE id = ?",
            (new_b, q["id"]),
        )
        apply_answer_to_streak(streak, correct, 5000)

    # Should be within +/- 80 points after 120 answers
    assert abs(estimated_theta - true_theta) < 80, f"theta={estimated_theta}, expected ~{true_theta}"

def test_flow_band_hit_rate_in_simulation():
    """>=60% of served questions should land in [0.65, 0.85]."""
    import random
    random.seed(7)
    conn = _mem_db()
    _seed_questions(conn, n=80)

    true_theta = 1050
    student_answer = _simulated_student(true_theta)
    estimated_theta = CFG.INITIAL_THETA
    streak = StreakState()
    in_band = 0
    total = 150

    for _ in range(total):
        q = select_next_question(conn, 1, 1, estimated_theta, streak)
        assert q is not None
        if 0.65 <= q["_expected_p"] <= 0.85:
            in_band += 1
        correct = student_answer(q["elo_b"])
        estimated_theta, new_b, _ = elo_update(
            estimated_theta, q["elo_b"], correct,
            q.get("times_answered") or 0,
        )
        conn.execute(
            "UPDATE questions SET elo_b = ?, times_answered = times_answered + 1 WHERE id = ?",
            (new_b, q["id"]),
        )
        apply_answer_to_streak(streak, correct, 5000)

    hit_rate = in_band / total
    assert hit_rate >= 0.60, f"hit rate = {hit_rate:.2f}, expected >= 0.60"

def test_rescue_mode_after_wrong_streak():
    """After 2 wrong answers, next question should have higher expected P."""
    import random
    random.seed(99)
    conn = _mem_db()
    _seed_questions(conn, n=80)

    streak = StreakState()
    apply_answer_to_streak(streak, False, 5000)
    apply_answer_to_streak(streak, False, 5000)

    q = select_next_question(conn, 1, 1, 1000, streak)
    assert q is not None
    # Rescue mode should pick an easier question (higher expected P)
    assert q["_expected_p"] >= 0.75, f"expected P = {q['_expected_p']:.2f}, rescue should be >= 0.75"

def test_telemetry_events_logged():
    """Every serve should log a flow_event."""
    conn = _mem_db()
    _seed_questions(conn, n=10)

    streak = StreakState()
    q = select_next_question(conn, 1, 1, 1000, streak)
    assert q is not None

    events = conn.execute("SELECT * FROM flow_events WHERE event_type = 'serve'").fetchall()
    assert len(events) == 1
    event = dict(events[0])
    assert event["student_id"] == 1
    assert event["question_id"] == q["id"]
    assert event["skill_id"] == 1
