# AutoTutor — Autonomous Flow Engine Optimizer

Inspired by [karpathy/autoresearch](https://github.com/karpathy/autoresearch): give an AI agent the Flow Engine parameters, let it experiment autonomously, and wake up to a better adaptive learning engine.

## How it works

| File | Role | Who modifies? |
|------|------|---------------|
| `prepare.py` | Student profiles, DB setup, metrics, evaluation | Fixed (human) |
| `engine.py` | FlowConfig parameters + algorithms + simulation | **Agent modifies this** |
| `run_experiments.py` | Batch sweep + experiment orchestrator | Fixed (human) |
| `program.md` | Agent instructions (the "skill") | Human iterates |

The agent modifies `engine.py` (parameters and/or algorithms), runs a simulation of 50 students x 5 sessions each, and checks if the **composite score** improved. Keep or discard. Repeat.

## Quick start

```bash
cd autotutor

# 1. Run baseline experiment (~0.5s)
python engine.py

# 2. Run full parameter sweep (~15s, 49 experiments)
python run_experiments.py --sweep --students 30

# 3. Point your AI agent at program.md and let it go
```

## Metrics

The composite score combines:
- **Flow Rate** (30w): % of questions in optimal difficulty band [0.65, 0.85]
- **Mastery Rate** (25w): % of sessions where student achieves >= 80% accuracy
- **Engagement Score** (0.25w): Composite of flow, accuracy optimality, low frustration, learning
- **Theta Gain**: How much the Elo estimate improved (learning signal)
- **Frustration Penalty** (-0.5 per event): Times a student hit frustration threshold

## Student Profiles

10 archetypes spanning Kinder (ages 5-6) and 4to Grado (ages 9-10):
- Varying ability levels (theta 600-1400)
- Different learning rates, consistency, frustration thresholds
- Realistic answer time distributions

## Phase 2 (Future)

Once the Panama pilot generates real student data:
1. Calibrate simulator profiles against real session data
2. Use real flow_events to validate simulator accuracy
3. Run overnight optimization with calibrated simulator
4. A/B test best config vs production config
