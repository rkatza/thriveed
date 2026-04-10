# ThriveEd Flow Engine — Runbook

## Overview

The Flow Engine is an Elo-based adaptive difficulty system that replaces the previous discrete difficulty (1-4) with continuous ratings. It keeps students in the "flow zone" where questions are challenging but achievable.

## How It Works

### Elo Ratings
- **Student ability (`theta`)**: Per (student, skill) pair. Starts at 1000. Increases on correct answers, decreases on incorrect.
- **Question difficulty (`elo_b`)**: Per question. Auto-calibrates from student responses. Higher = harder.
- **Expected P(correct)**: `1 / (1 + 10^((elo_b - theta) / 400))`

### Flow Zone
The selector targets questions where the student has a 70-80% chance of answering correctly:
- **Normal mode**: P(correct) in [0.70, 0.80]
- **Rescue mode** (2+ wrong in a row): P(correct) in [0.80, 0.90] — easier questions to rebuild confidence
- **Stretch mode** (3+ right fast <10s): P(correct) in [0.60, 0.70] — harder questions to challenge

### Forgetting Curve
- Each (student, skill) tracks `half_life_days` and `strength`
- `strength` decays exponentially: `strength(t) = strength * exp(-days / half_life)`
- Correct answer: `half_life *= 1.5` (capped at 90 days)
- Wrong answer: `half_life *= 0.5` (floor at 0.5 days)
- When `strength < 0.6`, skill becomes eligible for spaced-repetition review

## Tunables

All live in `FlowConfig` in `app/services/flow_engine.py`:

| Parameter | Default | Effect |
|-----------|---------|--------|
| `P_MIN` / `P_MAX` | 0.70 / 0.80 | Flow zone target range |
| `K_STUDENT` | 32.0 | How fast theta moves per answer |
| `K_QUESTION_BASE` | 16.0 | How fast elo_b moves (damped with attempts) |
| `CALIBRATION_ANCHOR` | 50 | K_question halves at this many attempts |
| `HALF_LIFE_ON_CORRECT` | 1.5 | Half-life multiplier on correct |
| `HALF_LIFE_ON_WRONG` | 0.5 | Half-life multiplier on wrong |
| `STRENGTH_REVIEW_THRESHOLD` | 0.60 | Strength below this triggers review |
| `RESCUE_AFTER_WRONG_IN_ROW` | 2 | Wrong streak to trigger rescue mode |
| `STRETCH_AFTER_RIGHT_IN_ROW` | 3 | Right streak (fast) to trigger stretch |
| `STRETCH_FAST_ANSWER_MS` | 10,000 | Max answer time (ms) for stretch mode |
| `BAND_WIDEN_STEP` | 0.05 | How much to widen band on each fallback |
| `MAX_WIDENING` | 4 | Max fallback iterations |

### Tuning Cheat Sheet

| I want | Change |
|--------|--------|
| Harder average experience | Lower `P_MIN`/`P_MAX` to 0.60/0.72 |
| Easier / more confidence-building | Raise to 0.75/0.85 |
| Faster student adaptation | Raise `K_STUDENT` to 48 |
| Faster question calibration | Raise `K_QUESTION_BASE` to 24 |
| Longer retention between reviews | Raise `HALF_LIFE_ON_CORRECT` to 2.0 |
| More aggressive rescue | Lower `RESCUE_AFTER_WRONG_IN_ROW` to 1 |
| More aggressive stretch | Lower `STRETCH_AFTER_RIGHT_IN_ROW` to 2 |

## Telemetry

The `flow_events` table logs every question served and answered:

```sql
-- Questions served in the flow zone
SELECT COUNT(*) as total,
       SUM(CASE WHEN expected_p BETWEEN 0.65 AND 0.85 THEN 1 ELSE 0 END) as in_band,
       ROUND(100.0 * SUM(CASE WHEN expected_p BETWEEN 0.65 AND 0.85 THEN 1 ELSE 0 END) / COUNT(*), 1) as pct
  FROM flow_events
 WHERE event_type = 'serve';

-- Selector fallback rate (question bank too thin)
SELECT COUNT(*) as total,
       SUM(CASE WHEN selector_fallback > 0 THEN 1 ELSE 0 END) as fallbacks,
       ROUND(100.0 * SUM(CASE WHEN selector_fallback > 0 THEN 1 ELSE 0 END) / COUNT(*), 1) as pct
  FROM flow_events
 WHERE event_type = 'serve';

-- Theta convergence per student
SELECT student_id, skill_id,
       MIN(theta_at) as min_theta, MAX(theta_at) as max_theta,
       AVG(theta_at) as avg_theta, COUNT(*) as answers
  FROM flow_events
 WHERE event_type = 'answer'
 GROUP BY student_id, skill_id;
```

## Migration

Run the migration script:
```bash
sqlite3 /data/app.db < migrations/001_elo_flow_engine.sql
```

Run the backfill script:
```bash
python scripts/backfill_elo.py /data/app.db
```

## Running Tests

```bash
cd alpha-school-backend
python -m pytest tests/test_flow_engine.py -v
```
