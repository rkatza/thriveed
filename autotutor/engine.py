"""
AutoTutor — engine.py
---------------------
This is the file the AI agent MODIFIES.
It contains the FlowConfig parameters and the simulation runner.

The agent experiments by changing the config values, running simulations,
and checking if the composite score improved.

Equivalent to autoresearch's train.py.
"""

from __future__ import annotations

import math
import random
import sqlite3
from dataclasses import dataclass, asdict
from typing import Optional

from prepare import (
    StudentProfile,
    SessionMetrics,
    ExperimentResult,
    create_sim_db,
    generate_profiles,
    make_student_answer_fn,
    QUESTIONS_PER_SESSION,
    EVAL_SESSIONS_PER_STUDENT,
    NUM_SKILLS,
)


# ══════════════════════════════════════════════════════════════════════════════
# TUNABLE PARAMETERS — The agent modifies these values
# ══════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class FlowConfig:
    """All tunable parameters for the adaptive engine."""

    # ── Flow band targets ──
    # The "zone of flow": target P(correct) range for question selection.
    # Questions are selected so the student has this probability of getting
    # them right. Too easy = boredom, too hard = frustration.
    P_MIN: float = 0.70
    P_MAX: float = 0.80

    # Rescue mode: after N wrong in a row, widen to easier questions
    P_MIN_RESCUE: float = 0.80
    P_MAX_STRETCH: float = 0.70

    # ── Elo constants ──
    # How fast student ability (theta) and question difficulty (elo_b) update
    INITIAL_THETA: float = 1000.0
    INITIAL_B: float = 1000.0
    K_STUDENT: float = 32.0          # student theta learning rate
    K_QUESTION_BASE: float = 16.0    # question elo_b learning rate
    ELO_DIVISOR: float = 400.0       # Elo scale factor

    # Calibration: K_question halves after this many attempts on a question
    CALIBRATION_ANCHOR: int = 50

    # ── Forgetting curve ──
    HALF_LIFE_INIT_DAYS: float = 1.0
    HALF_LIFE_CAP_DAYS: float = 90.0
    HALF_LIFE_ON_CORRECT: float = 1.5   # multiply half-life by this on correct
    HALF_LIFE_ON_WRONG: float = 0.5     # multiply half-life by this on wrong
    STRENGTH_REVIEW_THRESHOLD: float = 0.60

    # ── Streak triggers ──
    RESCUE_AFTER_WRONG_IN_ROW: int = 2
    STRETCH_AFTER_RIGHT_IN_ROW: int = 3
    STRETCH_FAST_ANSWER_MS: int = 10_000

    # ── Selector ──
    BAND_WIDEN_STEP: float = 0.05
    MAX_WIDENING: int = 4


CFG = FlowConfig()


# ══════════════════════════════════════════════════════════════════════════════
# ENGINE FUNCTIONS — The agent may also modify these algorithms
# ══════════════════════════════════════════════════════════════════════════════

def expected_p_correct(theta: float, elo_b: float) -> float:
    """Standard Elo expected score."""
    return 1.0 / (1.0 + 10.0 ** ((elo_b - theta) / CFG.ELO_DIVISOR))


def question_k_factor(times_answered: int) -> float:
    """Damp question movement as it calibrates."""
    damping = CFG.CALIBRATION_ANCHOR / (CFG.CALIBRATION_ANCHOR + times_answered)
    return max(2.0, CFG.K_QUESTION_BASE * damping)


def elo_update(
    theta: float, elo_b: float, was_correct: bool, times_answered: int
) -> tuple[float, float, float]:
    """Return (new_theta, new_elo_b, expected_p)."""
    expected = expected_p_correct(theta, elo_b)
    outcome = 1.0 if was_correct else 0.0
    kq = question_k_factor(times_answered)
    new_theta = theta + CFG.K_STUDENT * (outcome - expected)
    new_elo_b = elo_b + kq * (expected - outcome)
    return new_theta, new_elo_b, expected


@dataclass
class StreakState:
    wrong_in_row: int = 0
    right_in_row: int = 0
    last_answer_ms: Optional[int] = None


def current_flow_band(streak: StreakState) -> tuple[float, float]:
    """Return (p_min, p_max) adjusted by rescue/stretch streaks."""
    p_min, p_max = CFG.P_MIN, CFG.P_MAX
    if streak.wrong_in_row >= CFG.RESCUE_AFTER_WRONG_IN_ROW:
        p_min, p_max = CFG.P_MIN_RESCUE, CFG.P_MIN_RESCUE + 0.10
    elif (
        streak.right_in_row >= CFG.STRETCH_AFTER_RIGHT_IN_ROW
        and (streak.last_answer_ms or 999_999) < CFG.STRETCH_FAST_ANSWER_MS
    ):
        p_min, p_max = CFG.P_MAX_STRETCH - 0.10, CFG.P_MAX_STRETCH
    return p_min, p_max


def apply_answer_to_streak(streak: StreakState, was_correct: bool, time_ms: int) -> None:
    if was_correct:
        streak.right_in_row += 1
        streak.wrong_in_row = 0
    else:
        streak.wrong_in_row += 1
        streak.right_in_row = 0
    streak.last_answer_ms = time_ms


def _band_to_elo_range(theta: float, p_min: float, p_max: float) -> tuple[float, float]:
    """Convert probability band to elo_b range."""
    def b_for(p: float) -> float:
        p = min(max(p, 1e-4), 1 - 1e-4)
        return theta - CFG.ELO_DIVISOR * math.log10(p / (1 - p))
    b_high = b_for(p_min)
    b_low = b_for(p_max)
    return (b_low, b_high)


def select_next_question(
    conn: sqlite3.Connection,
    student_id: int,
    skill_id: int,
    theta: float,
    streak: StreakState,
    exclude_ids: Optional[set[int]] = None,
) -> Optional[dict]:
    """Select next question in the flow band for this student."""
    p_min, p_max = current_flow_band(streak)
    exclude_ids = exclude_ids or set()

    rows: list[dict] = []
    for widen in range(CFG.MAX_WIDENING + 1):
        adj_min = max(0.05, p_min - widen * CFG.BAND_WIDEN_STEP)
        adj_max = min(0.95, p_max + widen * CFG.BAND_WIDEN_STEP)
        b_low, b_high = _band_to_elo_range(theta, adj_min, adj_max)

        cur = conn.execute(
            """SELECT * FROM questions
               WHERE skill_id = ? AND is_placement = 0
                 AND COALESCE(needs_review, 0) = 0
                 AND elo_b BETWEEN ? AND ?
               ORDER BY times_answered ASC, id ASC
               LIMIT 25""",
            (skill_id, b_low, b_high),
        )
        rows = [dict(r) for r in cur.fetchall() if r["id"] not in exclude_ids]
        if rows:
            break

    if not rows:
        # Ultimate fallback: any question in this skill
        cur = conn.execute(
            "SELECT * FROM questions WHERE skill_id = ? AND is_placement = 0 LIMIT 10",
            (skill_id,),
        )
        rows = [dict(r) for r in cur.fetchall() if r["id"] not in exclude_ids]
        if not rows:
            return None

    rows.sort(key=lambda r: (r.get("times_answered") or 0, r["id"]))
    chosen = rows[0]
    chosen["_expected_p"] = expected_p_correct(theta, chosen["elo_b"])
    return chosen


# ══════════════════════════════════════════════════════════════════════════════
# SIMULATION RUNNER
# ══════════════════════════════════════════════════════════════════════════════

def run_session(
    conn: sqlite3.Connection,
    profile: StudentProfile,
    skill_id: int,
    answer_fn,
    num_questions: int = QUESTIONS_PER_SESSION,
) -> SessionMetrics:
    """Simulate one study session for a student on a skill."""
    theta = CFG.INITIAL_THETA
    streak = StreakState()
    metrics = SessionMetrics(
        student_id=profile.id,
        skill_id=skill_id,
        theta_start=theta,
    )
    answered_ids: set[int] = set()

    for _ in range(num_questions):
        q = select_next_question(conn, profile.id, skill_id, theta, streak, answered_ids)
        if q is None:
            break

        answered_ids.add(q["id"])
        was_correct, time_ms = answer_fn(q["elo_b"], streak.wrong_in_row)

        # Check if in flow band
        if 0.65 <= q["_expected_p"] <= 0.85:
            metrics.in_flow_band += 1

        # Check frustration
        if streak.wrong_in_row >= profile.frustration_threshold:
            metrics.frustration_events += 1

        # Check rescue
        if streak.wrong_in_row >= CFG.RESCUE_AFTER_WRONG_IN_ROW:
            metrics.rescue_triggers += 1

        # Track max wrong streak
        if streak.wrong_in_row > metrics.max_wrong_streak:
            metrics.max_wrong_streak = streak.wrong_in_row

        # Update Elo
        new_theta, new_b, _ = elo_update(theta, q["elo_b"], was_correct,
                                          q.get("times_answered") or 0)
        theta = new_theta
        conn.execute(
            "UPDATE questions SET elo_b = ?, times_answered = times_answered + 1 WHERE id = ?",
            (new_b, q["id"]),
        )
        apply_answer_to_streak(streak, was_correct, time_ms)

        metrics.questions_answered += 1
        if was_correct:
            metrics.correct_count += 1
        metrics.total_time_ms += time_ms

    metrics.theta_end = theta
    return metrics


def run_experiment(
    config_name: str = "baseline",
    num_students: int = 50,
    sessions_per_student: int = EVAL_SESSIONS_PER_STUDENT,
    seed: int = 42,
) -> ExperimentResult:
    """
    Run a full experiment: generate students, simulate sessions, collect metrics.
    This is the main entry point called by the experiment runner.
    """
    rng = random.Random(seed)
    profiles = generate_profiles(num_students, seed=seed)
    result = ExperimentResult(
        config_name=config_name,
        config_params=asdict(CFG),
    )

    for profile in profiles:
        conn = create_sim_db(seed=seed + profile.id)
        answer_fn = make_student_answer_fn(profile, rng)

        for session_num in range(sessions_per_student):
            skill_id = (session_num % NUM_SKILLS) + 1
            metrics = run_session(conn, profile, skill_id, answer_fn)
            result.session_metrics.append(metrics)

        conn.close()

    return result


# ══════════════════════════════════════════════════════════════════════════════
# MAIN — Run a single experiment and print results
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import time
    print("🧪 AutoTutor — Running experiment...")
    print(f"Config: {asdict(CFG)}\n")

    t0 = time.time()
    result = run_experiment(config_name="current")
    elapsed = time.time() - t0

    print(result.summary())
    print(f"\n⏱  Completed in {elapsed:.1f}s")
