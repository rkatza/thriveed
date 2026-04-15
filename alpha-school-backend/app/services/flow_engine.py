"""
Thriveed Flow Engine
--------------------
Elo-style adaptive difficulty + forgetting curve.

Design:
  - Each (student, skill) has theta (ability), half_life_days, strength.
  - Each question has elo_b (difficulty), times_answered, times_correct.
  - On answer we update both theta and elo_b with the Elo rule.
  - On answer we also update half_life / strength (Half-Life Regression style).
  - The selector picks the next question whose expected P(correct) is in
    the flow band [P_MIN, P_MAX] for the student's current theta.

All tunables live in FlowConfig so ops can adjust without code changes
via env vars later.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional


# ---------- Configuration ------------------------------------------------

@dataclass(frozen=True)
class FlowConfig:
    # Flow band targets
    P_MIN: float = 0.70
    P_MAX: float = 0.80
    P_MIN_RESCUE: float = 0.80   # widen easier after 2 wrong in a row
    P_MAX_STRETCH: float = 0.70  # widen harder after 3 right in a row fast

    # Elo constants
    INITIAL_THETA: float = 1000.0
    INITIAL_B: float = 1000.0
    K_STUDENT: float = 32.0      # how fast theta moves
    K_QUESTION_BASE: float = 16.0  # how fast elo_b moves (damped more than theta)
    ELO_DIVISOR: float = 400.0

    # Calibration damping: once a question has many attempts, move it less
    CALIBRATION_ANCHOR: int = 50  # K_question halves at this many attempts

    # Forgetting
    HALF_LIFE_INIT_DAYS: float = 1.0
    HALF_LIFE_CAP_DAYS: float = 90.0
    HALF_LIFE_ON_CORRECT: float = 1.5
    HALF_LIFE_ON_WRONG: float = 0.5
    STRENGTH_REVIEW_THRESHOLD: float = 0.60

    # Rescue / stretch streak triggers
    RESCUE_AFTER_WRONG_IN_ROW: int = 2
    STRETCH_AFTER_RIGHT_IN_ROW: int = 3
    STRETCH_FAST_ANSWER_MS: int = 10_000

    # Selector
    BAND_WIDEN_STEP: float = 0.05
    MAX_WIDENING: int = 4


CFG = FlowConfig()

# Grade-specific configurations (PRD §14.6)
KINDER_CFG = FlowConfig(
    P_MIN=0.75,
    P_MAX=0.88,
    P_MIN_RESCUE=0.88,
    P_MAX_STRETCH=0.75,
    K_STUDENT=20.0,
    RESCUE_AFTER_WRONG_IN_ROW=1,
    STRETCH_AFTER_RIGHT_IN_ROW=4,
    STRETCH_FAST_ANSWER_MS=15_000,
)

_GRADE_CONFIGS: dict[str, FlowConfig] = {
    "kinder": KINDER_CFG,
    "K": KINDER_CFG,
    "4to_grado": CFG,
    "4": CFG,
}


def config_for_grade(grade_level: str) -> FlowConfig:
    """Return the FlowConfig tuned for *grade_level*.

    Falls back to the default (4to grado) config for unknown grades.
    """
    return _GRADE_CONFIGS.get(grade_level, CFG)


# ---------- Elo core -----------------------------------------------------

def expected_p_correct(theta: float, elo_b: float) -> float:
    """Standard Elo expected score."""
    return 1.0 / (1.0 + 10.0 ** ((elo_b - theta) / CFG.ELO_DIVISOR))


def question_k_factor(times_answered: int) -> float:
    """Damp question movement as it calibrates. Never below 2.0."""
    damping = CFG.CALIBRATION_ANCHOR / (CFG.CALIBRATION_ANCHOR + times_answered)
    return max(2.0, CFG.K_QUESTION_BASE * damping)


def elo_update(
    theta: float,
    elo_b: float,
    was_correct: bool,
    times_answered_before: int,
) -> tuple[float, float, float]:
    """
    Return (new_theta, new_elo_b, expected_p).
    """
    expected = expected_p_correct(theta, elo_b)
    outcome = 1.0 if was_correct else 0.0

    kq = question_k_factor(times_answered_before)

    new_theta = theta + CFG.K_STUDENT * (outcome - expected)
    # Question moves in the opposite direction
    new_elo_b = elo_b + kq * (expected - outcome)

    return new_theta, new_elo_b, expected


# ---------- Forgetting curve ---------------------------------------------

def decayed_strength(
    last_strength: float,
    half_life_days: float,
    last_practiced_at: Optional[datetime],
    now: Optional[datetime] = None,
) -> float:
    """Apply exponential decay since last practice."""
    if last_practiced_at is None or half_life_days <= 0:
        return last_strength
    now = now or datetime.now(timezone.utc)
    if last_practiced_at.tzinfo is None:
        last_practiced_at = last_practiced_at.replace(tzinfo=timezone.utc)
    delta_days = max(0.0, (now - last_practiced_at).total_seconds() / 86400.0)
    return last_strength * math.exp(-delta_days / half_life_days)


def update_half_life(
    current_half_life: float,
    was_correct: bool,
) -> float:
    if was_correct:
        return min(CFG.HALF_LIFE_CAP_DAYS, current_half_life * CFG.HALF_LIFE_ON_CORRECT)
    return max(0.5, current_half_life * CFG.HALF_LIFE_ON_WRONG)


def update_strength(was_correct: bool) -> float:
    """After practicing, strength is reset toward 1 (correct) or 0.5 (wrong)."""
    return 1.0 if was_correct else 0.5


# ---------- Flow-band logic ----------------------------------------------

@dataclass
class StreakState:
    wrong_in_row: int = 0
    right_in_row: int = 0
    last_answer_ms: Optional[int] = None


def current_flow_band(
    streak: StreakState,
    cfg: FlowConfig | None = None,
) -> tuple[float, float]:
    """Return (p_min, p_max) adjusted by rescue/stretch streaks."""
    cfg = cfg or CFG
    p_min, p_max = cfg.P_MIN, cfg.P_MAX

    if streak.wrong_in_row >= cfg.RESCUE_AFTER_WRONG_IN_ROW:
        # Rescue: easier questions
        p_min, p_max = cfg.P_MIN_RESCUE, cfg.P_MIN_RESCUE + 0.10
    elif (
        streak.right_in_row >= cfg.STRETCH_AFTER_RIGHT_IN_ROW
        and (streak.last_answer_ms or 999_999) < cfg.STRETCH_FAST_ANSWER_MS
    ):
        # Stretch: harder questions
        p_min, p_max = cfg.P_MAX_STRETCH - 0.10, cfg.P_MAX_STRETCH

    return p_min, p_max


def apply_answer_to_streak(streak: StreakState, was_correct: bool, time_ms: int) -> None:
    if was_correct:
        streak.right_in_row += 1
        streak.wrong_in_row = 0
    else:
        streak.wrong_in_row += 1
        streak.right_in_row = 0
    streak.last_answer_ms = time_ms
