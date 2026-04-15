"""
Next-question selector. Queries SQLite directly for speed.

Strategy:
  1. Compute flow band [p_min, p_max].
  2. Convert band -> elo_b range given student theta.
  3. Pull candidate questions in that elo_b range, in the target skill,
     not answered in last 24h by this student.
  4. Prefer interest_tag matches, then lowest times_answered.
  5. Fall back by widening the band up to MAX_WIDENING times.
"""

from __future__ import annotations

import json
import math
import sqlite3
from typing import Optional

from app.services.flow_engine import (
    CFG,
    FlowConfig,
    StreakState,
    current_flow_band,
    expected_p_correct,
)


def _band_to_elo_range(
    theta: float, p_min: float, p_max: float, cfg: FlowConfig | None = None
) -> tuple[float, float]:
    """
    P = 1 / (1 + 10^((b-theta)/400))
    => b = theta - 400 * log10(P/(1-P))
    Higher P => easier => lower b.
    """
    elo_div = (cfg or CFG).ELO_DIVISOR

    def b_for(p: float) -> float:
        p = min(max(p, 1e-4), 1 - 1e-4)
        return theta - elo_div * math.log10(p / (1 - p))

    b_high = b_for(p_min)   # hardest acceptable
    b_low = b_for(p_max)    # easiest acceptable
    return (b_low, b_high)


def select_next_question(
    conn: sqlite3.Connection,
    student_id: int,
    skill_id: int,
    theta: float,
    streak: StreakState,
    interest_tags: Optional[list[str]] = None,
    session_id: Optional[str] = None,
    exclude_ids: Optional[set[int]] = None,
    cfg: Optional[FlowConfig] = None,
) -> Optional[dict]:
    cfg = cfg or CFG
    p_min, p_max = current_flow_band(streak, cfg)
    interest_tags = interest_tags or []
    exclude_ids = exclude_ids or set()

    rows = []
    fallback_used = 0
    for widen in range(cfg.MAX_WIDENING + 1):
        adj_min = max(0.05, p_min - widen * cfg.BAND_WIDEN_STEP)
        adj_max = min(0.95, p_max + widen * cfg.BAND_WIDEN_STEP)
        b_low, b_high = _band_to_elo_range(theta, adj_min, adj_max, cfg)

        cur = conn.execute(
            """
            SELECT q.*
              FROM questions q
             WHERE q.skill_id = ?
               AND q.is_placement = 0
               AND COALESCE(q.needs_review, 0) = 0
               AND q.elo_b BETWEEN ? AND ?
               AND q.id NOT IN (
                   SELECT question_id
                     FROM flow_events
                    WHERE student_id = ?
                      AND event_type = 'answer'
                      AND ts > datetime('now', '-1 day')
               )
          ORDER BY q.times_answered ASC, q.id ASC
             LIMIT 25
            """,
            (skill_id, b_low, b_high, student_id),
        )
        rows = [dict(r) for r in cur.fetchall() if r["id"] not in exclude_ids]
        if rows:
            break
        fallback_used = widen + 1

    if not rows:
        return None

    # Prefer interest-matched rows
    def tags_of(row: dict) -> set[str]:
        try:
            return set(json.loads(row.get("interest_tags") or "[]"))
        except Exception:
            return set()

    matched = [r for r in rows if tags_of(r) & set(interest_tags)]
    pool = matched or rows

    # Among the pool, prefer lowest times_answered (calibration coverage)
    pool.sort(key=lambda r: (r.get("times_answered") or 0, r["id"]))
    chosen = pool[0]

    expected = expected_p_correct(theta, chosen["elo_b"], cfg)

    # Telemetry
    conn.execute(
        """
        INSERT INTO flow_events (
            event_type, student_id, question_id, skill_id,
            theta_at, elo_b_at, expected_p,
            interest_match, selector_fallback, session_id
        ) VALUES ('serve', ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            student_id,
            chosen["id"],
            skill_id,
            theta,
            chosen["elo_b"],
            expected,
            1 if matched else 0,
            fallback_used,
            session_id,
        ),
    )
    chosen["_expected_p"] = expected
    chosen["_fallback"] = fallback_used
    return chosen
