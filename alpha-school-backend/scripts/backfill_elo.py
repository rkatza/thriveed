"""
Idempotent backfill:
  1. Initialize elo_b from legacy difficulty if still at default.
  2. Initialize theta = 1000 for any mastery_signals row missing it.
  3. Initialize half_life_days and strength for existing rows.
"""

import sqlite3
import sys
import os

# Add parent directory to path so we can import app modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.flow_engine import CFG


def main(db_path: str):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    # Backfill elo_b from legacy difficulty column
    result = conn.execute("""
        UPDATE questions
           SET elo_b = 800 + (COALESCE(difficulty, 2) * 100)
         WHERE elo_b IS NULL OR elo_b = 1000.0
    """)
    print(f"Updated {result.rowcount} questions with elo_b from difficulty.")

    # Backfill theta for mastery_signals
    result = conn.execute("""
        UPDATE mastery_signals
           SET theta = ?
         WHERE theta IS NULL
    """, (CFG.INITIAL_THETA,))
    print(f"Updated {result.rowcount} mastery rows with theta={CFG.INITIAL_THETA}.")

    # Backfill half_life_days
    result = conn.execute("""
        UPDATE mastery_signals
           SET half_life_days = ?
         WHERE half_life_days IS NULL
    """, (CFG.HALF_LIFE_INIT_DAYS,))
    print(f"Updated {result.rowcount} mastery rows with half_life_days={CFG.HALF_LIFE_INIT_DAYS}.")

    # Backfill strength
    result = conn.execute("""
        UPDATE mastery_signals
           SET strength = 1.0
         WHERE strength IS NULL
    """)
    print(f"Updated {result.rowcount} mastery rows with strength=1.0.")

    # Initialize times_answered / times_correct for questions
    result = conn.execute("""
        UPDATE questions
           SET times_answered = COALESCE(times_answered, 0),
               times_correct = COALESCE(times_correct, 0),
               needs_review = COALESCE(needs_review, 0)
         WHERE times_answered IS NULL OR times_correct IS NULL
    """)
    print(f"Updated {result.rowcount} questions with times_answered/times_correct defaults.")

    conn.commit()
    conn.close()
    print("Backfill complete.")


if __name__ == "__main__":
    db_path = sys.argv[1] if len(sys.argv) > 1 else "/data/app.db"
    main(db_path)
