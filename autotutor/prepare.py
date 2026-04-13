"""
AutoTutor — prepare.py
----------------------
Fixed constants, student profile generation, and evaluation utilities.
This file is NOT modified by the agent. It provides the simulation
infrastructure that the agent's experiments run against.

Inspired by karpathy/autoresearch: the agent modifies engine.py,
this file stays fixed.
"""

from __future__ import annotations

import json
import math
import random
import sqlite3
import statistics
from dataclasses import dataclass, field, asdict
from typing import Optional


# ── Constants ──────────────────────────────────────────────────────────────

RANDOM_SEED = 42
NUM_SKILLS = 10
QUESTIONS_PER_SKILL = 30
TOTAL_QUESTIONS = NUM_SKILLS * QUESTIONS_PER_SKILL

# Evaluation
EVAL_SESSIONS_PER_STUDENT = 5   # each student does 5 study sessions
QUESTIONS_PER_SESSION = 15      # 15 questions per session
MASTERY_THRESHOLD = 0.80        # mastery = accuracy >= 80% on a skill


# ── Student Profiles ───────────────────────────────────────────────────────

@dataclass
class StudentProfile:
    """A simulated student with a true ability level and learning traits."""
    id: int
    name: str
    true_theta: float           # true ability (Elo scale, 600-1400)
    learning_rate: float        # how fast they improve (0.5=slow, 2.0=fast)
    consistency: float          # answer noise (0.0=random, 1.0=perfectly predictable)
    frustration_threshold: int  # wrong-in-row before "giving up" (random answers)
    age_group: str              # "kinder" or "4to_grado"
    speed_ms_mean: int          # avg answer time in ms
    speed_ms_std: int           # std dev of answer time


# Canonical student archetypes for the Panama pilot
STUDENT_PROFILES: list[StudentProfile] = [
    # -- Kinder students (lower theta range) --
    StudentProfile(1, "Ana (Kinder Avanzada)", 900, 1.5, 0.85, 5, "kinder", 8000, 3000),
    StudentProfile(2, "Luis (Kinder Promedio)", 750, 1.0, 0.70, 3, "kinder", 12000, 5000),
    StudentProfile(3, "Mía (Kinder Lenta)", 600, 0.6, 0.60, 2, "kinder", 15000, 6000),
    StudentProfile(4, "Carlos (Kinder Inconsistente)", 800, 1.2, 0.50, 4, "kinder", 10000, 4000),

    # -- 4to Grado students (higher theta range) --
    StudentProfile(5, "Sofía (4to Estrella)", 1300, 1.8, 0.90, 6, "4to_grado", 5000, 2000),
    StudentProfile(6, "Diego (4to Promedio)", 1050, 1.0, 0.75, 3, "4to_grado", 8000, 3000),
    StudentProfile(7, "Valentina (4to Luchadora)", 850, 0.7, 0.65, 2, "4to_grado", 12000, 5000),
    StudentProfile(8, "Mateo (4to Rápido/Descuidado)", 1100, 1.3, 0.55, 4, "4to_grado", 4000, 1500),
    StudentProfile(9, "Camila (4to Ansiosa)", 950, 0.9, 0.70, 2, "4to_grado", 14000, 6000),
    StudentProfile(10, "Santiago (4to Alto Nivel)", 1400, 2.0, 0.92, 8, "4to_grado", 4000, 1000),
]


def generate_profiles(n: int = 100, seed: int = RANDOM_SEED) -> list[StudentProfile]:
    """
    Generate n student profiles by sampling around the archetypes.
    Produces a realistic distribution of abilities and learning styles.
    """
    rng = random.Random(seed)
    profiles = []
    for i in range(n):
        # Pick a random archetype to base this student on
        archetype = rng.choice(STUDENT_PROFILES)
        profiles.append(StudentProfile(
            id=i + 1,
            name=f"Student_{i+1}",
            true_theta=max(400, min(1600, rng.gauss(archetype.true_theta, 80))),
            learning_rate=max(0.3, min(2.5, rng.gauss(archetype.learning_rate, 0.2))),
            consistency=max(0.3, min(1.0, rng.gauss(archetype.consistency, 0.1))),
            frustration_threshold=max(1, int(rng.gauss(archetype.frustration_threshold, 1))),
            age_group=archetype.age_group,
            speed_ms_mean=max(2000, int(rng.gauss(archetype.speed_ms_mean, 2000))),
            speed_ms_std=max(500, int(rng.gauss(archetype.speed_ms_std, 1000))),
        ))
    return profiles


# ── In-Memory Database ─────────────────────────────────────────────────────

def create_sim_db(num_skills: int = NUM_SKILLS,
                  questions_per_skill: int = QUESTIONS_PER_SKILL,
                  seed: int = RANDOM_SEED) -> sqlite3.Connection:
    """Create an in-memory SQLite DB with questions spread across skills."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row

    conn.executescript("""
        CREATE TABLE questions (
            id INTEGER PRIMARY KEY,
            skill_id INTEGER,
            question_text TEXT,
            question_type TEXT DEFAULT 'mc',
            options TEXT DEFAULT '[]',
            correct_answer TEXT DEFAULT 'A',
            hint TEXT,
            explanation TEXT,
            difficulty INTEGER DEFAULT 1,
            is_placement INTEGER DEFAULT 0,
            interest_tags TEXT DEFAULT '[]',
            elo_b REAL DEFAULT 1000.0,
            times_answered INTEGER DEFAULT 0,
            times_correct INTEGER DEFAULT 0,
            needs_review INTEGER DEFAULT 0
        );
        CREATE TABLE flow_events (
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
        CREATE INDEX idx_flow_events_student ON flow_events(student_id, ts);
        CREATE INDEX idx_questions_skill_elo ON questions(skill_id, elo_b);
    """)

    rng = random.Random(seed)
    qid = 1
    for skill_id in range(1, num_skills + 1):
        for j in range(questions_per_skill):
            # Spread elo_b from 500 to 1500 across questions
            elo_b = 500 + (1000 * j / max(1, questions_per_skill - 1))
            # Add some randomness
            elo_b += rng.gauss(0, 50)
            conn.execute(
                """INSERT INTO questions
                     (id, skill_id, question_text, question_type, options,
                      correct_answer, elo_b, difficulty)
                   VALUES (?, ?, ?, 'mc', '["A","B","C","D"]', 'A', ?, ?)""",
                (qid, skill_id, f"Q{qid}_S{skill_id}", elo_b,
                 1 + j * 5 // questions_per_skill),
            )
            qid += 1
    conn.commit()
    return conn


# ── Simulated Student Answer Function ──────────────────────────────────────

def make_student_answer_fn(profile: StudentProfile, rng: random.Random):
    """
    Return a function(elo_b, wrong_streak) -> (was_correct, time_ms).

    The student's P(correct) is based on:
    1. Elo formula: base_p = 1 / (1 + 10^((elo_b - theta) / 400))
    2. Consistency noise: actual_p = consistency * base_p + (1-consistency) * 0.5
    3. Frustration: if wrong_streak >= threshold, answers randomly (p=0.25)
    4. Learning: theta drifts toward true_theta over time
    """
    current_theta = [profile.true_theta]  # mutable closure

    def answer(elo_b: float, wrong_streak: int = 0) -> tuple[bool, int]:
        # Frustration check
        if wrong_streak >= profile.frustration_threshold:
            was_correct = rng.random() < 0.25  # random guessing
            time_ms = max(1000, int(rng.gauss(profile.speed_ms_mean * 0.5, 1000)))
            return was_correct, time_ms

        # Base Elo probability
        base_p = 1.0 / (1.0 + 10.0 ** ((elo_b - current_theta[0]) / 400.0))

        # Consistency-adjusted probability
        actual_p = profile.consistency * base_p + (1 - profile.consistency) * 0.5

        was_correct = rng.random() < actual_p

        # Learning effect: theta drifts slightly toward true ability
        if was_correct:
            current_theta[0] += profile.learning_rate * 2
        else:
            current_theta[0] -= profile.learning_rate * 0.5

        # Answer time
        time_ms = max(1000, int(rng.gauss(profile.speed_ms_mean, profile.speed_ms_std)))
        if not was_correct:
            time_ms = int(time_ms * 1.3)  # wrong answers take longer

        return was_correct, time_ms

    return answer


# ── Evaluation Metrics ─────────────────────────────────────────────────────

@dataclass
class SessionMetrics:
    """Metrics for a single student session."""
    student_id: int
    skill_id: int
    questions_answered: int = 0
    correct_count: int = 0
    in_flow_band: int = 0       # questions where expected_p was in [0.65, 0.85]
    rescue_triggers: int = 0     # times rescue mode activated
    frustration_events: int = 0  # times student hit frustration threshold
    total_time_ms: int = 0
    theta_start: float = 0.0
    theta_end: float = 0.0
    max_wrong_streak: int = 0

    @property
    def accuracy(self) -> float:
        return self.correct_count / max(1, self.questions_answered)

    @property
    def flow_rate(self) -> float:
        return self.in_flow_band / max(1, self.questions_answered)

    @property
    def theta_gain(self) -> float:
        return self.theta_end - self.theta_start

    @property
    def avg_time_ms(self) -> float:
        return self.total_time_ms / max(1, self.questions_answered)


@dataclass
class ExperimentResult:
    """Aggregated metrics across all students and sessions."""
    config_name: str
    config_params: dict
    session_metrics: list[SessionMetrics] = field(default_factory=list)

    # ── Computed aggregates ──
    @property
    def num_sessions(self) -> int:
        return len(self.session_metrics)

    @property
    def mean_accuracy(self) -> float:
        accs = [s.accuracy for s in self.session_metrics]
        return statistics.mean(accs) if accs else 0.0

    @property
    def mean_flow_rate(self) -> float:
        rates = [s.flow_rate for s in self.session_metrics]
        return statistics.mean(rates) if rates else 0.0

    @property
    def mean_theta_gain(self) -> float:
        gains = [s.theta_gain for s in self.session_metrics]
        return statistics.mean(gains) if gains else 0.0

    @property
    def total_frustration_events(self) -> int:
        return sum(s.frustration_events for s in self.session_metrics)

    @property
    def total_rescue_triggers(self) -> int:
        return sum(s.rescue_triggers for s in self.session_metrics)

    @property
    def mastery_rate(self) -> float:
        """% of sessions where student achieved >= MASTERY_THRESHOLD accuracy."""
        if not self.session_metrics:
            return 0.0
        mastered = sum(1 for s in self.session_metrics if s.accuracy >= MASTERY_THRESHOLD)
        return mastered / len(self.session_metrics)

    @property
    def engagement_score(self) -> float:
        """
        Composite engagement score (0-100):
        - 40% flow rate (questions in optimal difficulty band)
        - 30% accuracy (not too easy, not too hard)
        - 20% low frustration (few rescue triggers)
        - 10% learning (positive theta gain)
        """
        if not self.session_metrics:
            return 0.0

        flow_component = self.mean_flow_rate * 40

        # Accuracy: optimal is 0.70-0.85 (matches flow band)
        acc = self.mean_accuracy
        if 0.70 <= acc <= 0.85:
            acc_component = 30.0
        elif acc > 0.85:
            acc_component = 30.0 * (1.0 - (acc - 0.85) / 0.15)  # too easy
        else:
            acc_component = 30.0 * (acc / 0.70)  # too hard

        # Frustration: fewer is better
        frust_per_session = self.total_frustration_events / max(1, self.num_sessions)
        frust_component = max(0, 20.0 * (1.0 - frust_per_session / 3.0))

        # Learning: positive theta gain is good
        gain = self.mean_theta_gain
        learn_component = min(10.0, max(0.0, 10.0 * gain / 50.0))

        return flow_component + acc_component + frust_component + learn_component

    @property
    def composite_score(self) -> float:
        """
        Single number to optimize. Higher is better.
        Weighted combination of all metrics.
        This is the "val_bpb" equivalent — the number the agent tries to maximize.
        """
        return (
            self.mean_flow_rate * 30          # flow zone targeting
            + self.mastery_rate * 25          # students achieving mastery
            + self.engagement_score * 0.25    # engagement (already 0-100)
            + max(0, self.mean_theta_gain / 5)  # learning progress
            - self.total_frustration_events * 0.5  # frustration penalty
        )

    def summary(self) -> str:
        lines = [
            f"═══ Experiment: {self.config_name} ═══",
            f"  Sessions:           {self.num_sessions}",
            f"  Mean Accuracy:      {self.mean_accuracy:.3f}",
            f"  Mean Flow Rate:     {self.mean_flow_rate:.3f}",
            f"  Mastery Rate:       {self.mastery_rate:.3f}",
            f"  Mean Theta Gain:    {self.mean_theta_gain:.1f}",
            f"  Frustration Events: {self.total_frustration_events}",
            f"  Rescue Triggers:    {self.total_rescue_triggers}",
            f"  Engagement Score:   {self.engagement_score:.1f}/100",
            f"  ★ Composite Score:  {self.composite_score:.2f}",
        ]
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "config_name": self.config_name,
            "config_params": self.config_params,
            "num_sessions": self.num_sessions,
            "mean_accuracy": round(self.mean_accuracy, 4),
            "mean_flow_rate": round(self.mean_flow_rate, 4),
            "mastery_rate": round(self.mastery_rate, 4),
            "mean_theta_gain": round(self.mean_theta_gain, 2),
            "total_frustration_events": self.total_frustration_events,
            "total_rescue_triggers": self.total_rescue_triggers,
            "engagement_score": round(self.engagement_score, 2),
            "composite_score": round(self.composite_score, 4),
        }
