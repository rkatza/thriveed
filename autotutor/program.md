# AutoTutor — Agent Program

> *You are an AI research agent optimizing ThriveEd's adaptive learning engine.
> Your goal: find the parameter configuration that maximizes student learning outcomes
> for the Panama math pilot (Kinder + 4to Grado).*

## Context

ThriveEd uses an Elo-based "Flow Engine" to select questions at the right difficulty
for each student. The engine has ~20 tunable parameters that control:

- **Flow band**: The target P(correct) range for question selection (zone of flow)
- **Elo dynamics**: How fast student ability and question difficulty ratings update
- **Forgetting curve**: How quickly mastered skills decay and need review
- **Rescue/Stretch**: When to give easier questions (rescue) or harder ones (stretch)
- **Selector**: How aggressively to widen the search when no questions match

## Your Task

1. **Read** `engine.py` to understand the current FlowConfig parameters
2. **Run baseline**: `python engine.py` to see current performance
3. **Form a hypothesis** about which parameter change might improve the composite score
4. **Edit** `engine.py` — change one or more FlowConfig values (or modify the algorithms)
5. **Run** `python engine.py` to evaluate
6. **Compare** to baseline: if composite_score improved, KEEP. Otherwise, REVERT.
7. **Log** your experiment in `logs/experiments.md` with hypothesis, change, and result
8. **Repeat** from step 3

## Files

| File | Role | Modify? |
|------|------|---------|
| `prepare.py` | Student profiles, DB setup, metrics, evaluation | **NO** |
| `engine.py` | FlowConfig + engine algorithms + simulation runner | **YES** |
| `run_experiments.py` | Batch experiment runner + sweep | **NO** (but you can run it) |
| `program.md` | This file — your instructions | **NO** |

## Metric: Composite Score

The single number to maximize (higher = better):

```
composite_score = (
    mean_flow_rate * 30          # questions in optimal difficulty band
    + mastery_rate * 25          # students achieving >= 80% accuracy
    + engagement_score * 0.25    # engagement composite (0-100)
    + theta_gain / 5             # learning progress
    - frustration_events * 0.5   # frustration penalty
)
```

### Sub-metrics explained:
- **Flow Rate**: % of questions where expected P(correct) is in [0.65, 0.85]
- **Mastery Rate**: % of sessions where student accuracy >= 80%
- **Engagement Score**: Composite of flow rate, accuracy optimality, low frustration, learning
- **Theta Gain**: How much the Elo estimate improved (positive = learning)
- **Frustration Events**: Times a student hit their frustration threshold

## Constraints

- Do NOT change `prepare.py` (the evaluation infrastructure must stay fixed)
- Keep changes to `engine.py` only
- All parameters must be physically reasonable:
  - P_MIN/P_MAX must be in [0.0, 1.0] and P_MIN < P_MAX
  - K values must be positive
  - Half-life values must be positive
  - Streak thresholds must be >= 1
- The engine must still work with ThriveEd's production code (same API surface)

## Experiment Ideas to Try

### Quick wins (single parameter):
- [ ] Widen flow band: P_MIN=0.65, P_MAX=0.85
- [ ] Faster Elo adaptation: K_STUDENT=48
- [ ] More sensitive rescue: RESCUE_AFTER_WRONG_IN_ROW=1
- [ ] Wider selector: BAND_WIDEN_STEP=0.08

### Compound experiments:
- [ ] Kinder-optimized: higher P_MIN (easier), lower K_STUDENT (gentler)
- [ ] Challenge mode: lower P_MIN (harder), higher K_STUDENT (faster adaptation)
- [ ] Anti-frustration: rescue=1, gentle K, wide band

### Algorithm changes:
- [ ] Dynamic K_STUDENT that decreases as theta stabilizes
- [ ] Non-linear flow band that adapts to student consistency
- [ ] Weighted question selection (prefer questions near student's theta)

## How to Log Experiments

After each experiment, append to `logs/experiments.md`:

```markdown
### Experiment N: [name]
- **Hypothesis**: [why you think this will help]
- **Change**: [what you modified in engine.py]
- **Result**: score=X.XX (baseline=Y.YY, delta=+/-Z.ZZ)
- **Keep/Revert**: [KEEP/REVERT]
- **Insight**: [what you learned]
```

## Running Commands

```bash
# Single experiment with current config
python engine.py

# Full automated sweep (takes ~2-5 minutes)
python run_experiments.py --sweep --students 30

# Baseline only
python run_experiments.py --baseline --students 50
```

Good luck, agent. Make our students learn better. 🧠
