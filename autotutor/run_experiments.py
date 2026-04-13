"""
AutoTutor — run_experiments.py
------------------------------
Experiment runner: the autonomous loop that modifies engine.py parameters,
runs simulations, evaluates results, and keeps or discards changes.

This is the orchestrator — equivalent to running the agent in autoresearch.
An AI agent (or this script in sweep mode) iterates over parameter
configurations, evaluates each one, and tracks the best.

Usage:
    # Run baseline only
    python run_experiments.py --baseline

    # Run parameter sweep (automated optimization)
    python run_experiments.py --sweep

    # Run a specific named experiment from experiments.json
    python run_experiments.py --run "wider_flow_band"
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import sys
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Add parent to path so we can import engine
sys.path.insert(0, str(Path(__file__).parent))

from engine import FlowConfig, CFG, run_experiment, ExperimentResult
from prepare import ExperimentResult as PrepareExperimentResult


# ── Experiment Log ─────────────────────────────────────────────────────────

LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

RESULTS_FILE = LOG_DIR / "experiment_results.jsonl"
BEST_FILE = LOG_DIR / "best_config.json"


def log_result(result: ExperimentResult, elapsed_s: float) -> bool:
    """Append result to JSONL log and update best if improved."""
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "elapsed_s": round(elapsed_s, 2),
        **result.to_dict(),
    }
    with open(RESULTS_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")

    # Check if this is the new best
    best_score = -999
    if BEST_FILE.exists():
        with open(BEST_FILE) as f:
            best_data = json.load(f)
            best_score = best_data.get("composite_score", -999)

    if result.composite_score > best_score:
        with open(BEST_FILE, "w") as f:
            json.dump(entry, f, indent=2)
        print(f"  🏆 NEW BEST! Score: {result.composite_score:.4f} (prev: {best_score:.4f})")
        return True
    else:
        print(f"  ❌ Not better. Score: {result.composite_score:.4f} (best: {best_score:.4f})")
        return False


# ── Parameter Sweep Definitions ────────────────────────────────────────────

SWEEP_PARAMS: dict[str, list[Any]] = {
    # Flow band experiments
    "P_MIN": [0.60, 0.65, 0.70, 0.75],
    "P_MAX": [0.75, 0.80, 0.85, 0.90],

    # Elo learning rates
    "K_STUDENT": [16.0, 24.0, 32.0, 48.0, 64.0],
    "K_QUESTION_BASE": [8.0, 12.0, 16.0, 24.0],

    # Rescue sensitivity
    "RESCUE_AFTER_WRONG_IN_ROW": [1, 2, 3, 4],
    "STRETCH_AFTER_RIGHT_IN_ROW": [2, 3, 4, 5],

    # Selector widening
    "BAND_WIDEN_STEP": [0.03, 0.05, 0.08, 0.10],
    "MAX_WIDENING": [2, 3, 4, 6],

    # Forgetting curve
    "HALF_LIFE_ON_CORRECT": [1.2, 1.5, 2.0, 2.5],
    "HALF_LIFE_ON_WRONG": [0.3, 0.5, 0.7],
}


def _make_config(overrides: dict) -> FlowConfig:
    """Create a FlowConfig with overrides applied."""
    base = asdict(CFG)
    base.update(overrides)
    return FlowConfig(**base)


def _run_with_config(config: FlowConfig, name: str, num_students: int = 50) -> ExperimentResult:
    """Monkey-patch engine.CFG, run experiment, restore."""
    import engine
    original = engine.CFG
    engine.CFG = config
    try:
        result = run_experiment(config_name=name, num_students=num_students)
        result.config_params = asdict(config)
        return result
    finally:
        engine.CFG = original


# ── Run Modes ──────────────────────────────────────────────────────────────

def run_baseline(num_students: int = 50) -> ExperimentResult:
    """Run baseline experiment with default config."""
    print("═══ Running BASELINE experiment ═══")
    t0 = time.time()
    result = run_experiment(config_name="baseline", num_students=num_students)
    elapsed = time.time() - t0
    print(result.summary())
    print(f"⏱  {elapsed:.1f}s\n")
    log_result(result, elapsed)
    return result


def run_single_param_sweep(num_students: int = 30) -> list[ExperimentResult]:
    """Sweep each parameter independently while holding others at baseline."""
    print("═══ Running SINGLE-PARAMETER SWEEP ═══\n")
    all_results = []

    for param_name, values in SWEEP_PARAMS.items():
        print(f"─── Sweeping {param_name} ───")
        for value in values:
            # Skip if same as baseline
            baseline_val = getattr(CFG, param_name)
            is_baseline = (value == baseline_val)

            config = _make_config({param_name: value})
            name = f"{param_name}={value}" + (" (baseline)" if is_baseline else "")
            print(f"  Running: {name}...", end=" ", flush=True)

            t0 = time.time()
            result = _run_with_config(config, name, num_students)
            elapsed = time.time() - t0

            print(f"score={result.composite_score:.4f} ({elapsed:.1f}s)")
            log_result(result, elapsed)
            all_results.append(result)

        print()

    return all_results


def run_multi_param_experiments(num_students: int = 30) -> list[ExperimentResult]:
    """Run pre-defined multi-parameter experiments."""
    experiments = {
        "kinder_optimized": {
            "P_MIN": 0.75, "P_MAX": 0.88,
            "K_STUDENT": 24.0,
            "RESCUE_AFTER_WRONG_IN_ROW": 1,
            "HALF_LIFE_ON_CORRECT": 1.2,
        },
        "4to_grado_challenge": {
            "P_MIN": 0.65, "P_MAX": 0.78,
            "K_STUDENT": 48.0,
            "STRETCH_AFTER_RIGHT_IN_ROW": 2,
            "HALF_LIFE_ON_CORRECT": 2.0,
        },
        "aggressive_adaptation": {
            "K_STUDENT": 64.0, "K_QUESTION_BASE": 24.0,
            "BAND_WIDEN_STEP": 0.03,
            "MAX_WIDENING": 6,
        },
        "gentle_learning": {
            "K_STUDENT": 16.0, "K_QUESTION_BASE": 8.0,
            "P_MIN": 0.75, "P_MAX": 0.88,
            "RESCUE_AFTER_WRONG_IN_ROW": 1,
        },
        "wide_flow_band": {
            "P_MIN": 0.60, "P_MAX": 0.90,
            "BAND_WIDEN_STEP": 0.10,
        },
        "narrow_flow_band": {
            "P_MIN": 0.72, "P_MAX": 0.78,
            "BAND_WIDEN_STEP": 0.03,
        },
        "fast_forgetting": {
            "HALF_LIFE_ON_CORRECT": 1.2,
            "HALF_LIFE_ON_WRONG": 0.3,
            "STRENGTH_REVIEW_THRESHOLD": 0.70,
        },
        "slow_forgetting": {
            "HALF_LIFE_ON_CORRECT": 2.5,
            "HALF_LIFE_ON_WRONG": 0.7,
            "STRENGTH_REVIEW_THRESHOLD": 0.50,
        },
    }

    print("═══ Running MULTI-PARAMETER EXPERIMENTS ═══\n")
    all_results = []

    for exp_name, overrides in experiments.items():
        config = _make_config(overrides)
        print(f"  Running: {exp_name}...", end=" ", flush=True)

        t0 = time.time()
        result = _run_with_config(config, exp_name, num_students)
        elapsed = time.time() - t0

        print(f"score={result.composite_score:.4f} ({elapsed:.1f}s)")
        log_result(result, elapsed)
        all_results.append(result)

    return all_results


def run_full_sweep(num_students: int = 30):
    """Run everything: baseline, single sweep, multi-param experiments."""
    # 1. Baseline
    baseline = run_baseline(num_students)

    # 2. Single parameter sweep
    single_results = run_single_param_sweep(num_students)

    # 3. Multi-parameter experiments
    multi_results = run_multi_param_experiments(num_students)

    # 4. Summary
    all_results = [baseline] + single_results + multi_results
    all_results.sort(key=lambda r: r.composite_score, reverse=True)

    print("\n" + "═" * 70)
    print("TOP 10 CONFIGURATIONS")
    print("═" * 70)
    for i, r in enumerate(all_results[:10], 1):
        print(f"  {i}. {r.config_name:40s} score={r.composite_score:.4f}  "
              f"acc={r.mean_accuracy:.3f}  flow={r.mean_flow_rate:.3f}  "
              f"mastery={r.mastery_rate:.3f}")

    print(f"\n{'═' * 70}")
    print("WORST 5 CONFIGURATIONS")
    print("═" * 70)
    for i, r in enumerate(all_results[-5:], 1):
        print(f"  {i}. {r.config_name:40s} score={r.composite_score:.4f}  "
              f"acc={r.mean_accuracy:.3f}  flow={r.mean_flow_rate:.3f}  "
              f"mastery={r.mastery_rate:.3f}")

    # Load and display the best
    if BEST_FILE.exists():
        with open(BEST_FILE) as f:
            best = json.load(f)
        print(f"\n🏆 OVERALL BEST: {best['config_name']} "
              f"(score={best['composite_score']:.4f})")
        print(f"   Config: {json.dumps({k: v for k, v in best['config_params'].items() if v != asdict(FlowConfig())[k]}, indent=2)}")

    return all_results


def generate_report(results: list[ExperimentResult]) -> str:
    """Generate a markdown report of experiment results."""
    lines = [
        "# AutoTutor Phase 1 — Experiment Report",
        f"_Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}_\n",
        "## Overview",
        f"Total experiments run: {len(results)}",
        f"Student profiles per experiment: varies (30-50)\n",
        "## Top Configurations\n",
        "| Rank | Config | Score | Accuracy | Flow Rate | Mastery | Engagement |",
        "|------|--------|-------|----------|-----------|---------|------------|",
    ]

    sorted_results = sorted(results, key=lambda r: r.composite_score, reverse=True)
    for i, r in enumerate(sorted_results[:15], 1):
        lines.append(
            f"| {i} | {r.config_name} | {r.composite_score:.2f} | "
            f"{r.mean_accuracy:.3f} | {r.mean_flow_rate:.3f} | "
            f"{r.mastery_rate:.3f} | {r.engagement_score:.1f} |"
        )

    # Best config details
    best = sorted_results[0]
    baseline = next((r for r in results if r.config_name == "baseline"), sorted_results[-1])

    lines.extend([
        "\n## Best Configuration\n",
        f"**Name:** {best.config_name}",
        f"**Composite Score:** {best.composite_score:.4f}",
        f"**vs Baseline:** {best.composite_score - baseline.composite_score:+.4f}\n",
        "### Parameters (differences from baseline)\n",
        "```json",
    ])

    baseline_params = asdict(FlowConfig())
    diff_params = {k: v for k, v in best.config_params.items()
                   if v != baseline_params.get(k)}
    lines.append(json.dumps(diff_params, indent=2))
    lines.append("```\n")

    # Metrics comparison
    lines.extend([
        "### Metrics Comparison\n",
        "| Metric | Baseline | Best | Delta |",
        "|--------|----------|------|-------|",
        f"| Accuracy | {baseline.mean_accuracy:.3f} | {best.mean_accuracy:.3f} | {best.mean_accuracy - baseline.mean_accuracy:+.3f} |",
        f"| Flow Rate | {baseline.mean_flow_rate:.3f} | {best.mean_flow_rate:.3f} | {best.mean_flow_rate - baseline.mean_flow_rate:+.3f} |",
        f"| Mastery Rate | {baseline.mastery_rate:.3f} | {best.mastery_rate:.3f} | {best.mastery_rate - baseline.mastery_rate:+.3f} |",
        f"| Engagement | {baseline.engagement_score:.1f} | {best.engagement_score:.1f} | {best.engagement_score - baseline.engagement_score:+.1f} |",
        f"| Frustration | {baseline.total_frustration_events} | {best.total_frustration_events} | {best.total_frustration_events - baseline.total_frustration_events:+d} |",
        f"| Theta Gain | {baseline.mean_theta_gain:.1f} | {best.mean_theta_gain:.1f} | {best.mean_theta_gain - baseline.mean_theta_gain:+.1f} |",
    ])

    # Key insights
    lines.extend([
        "\n## Key Insights\n",
        "### What improved scores:",
    ])

    # Analyze which parameters helped
    param_effects: dict[str, list[tuple[float, Any]]] = {}
    for r in results:
        for param, baseline_val in baseline_params.items():
            exp_val = r.config_params.get(param)
            if exp_val is not None and exp_val != baseline_val:
                if param not in param_effects:
                    param_effects[param] = []
                param_effects[param].append((r.composite_score - baseline.composite_score, exp_val))

    for param, effects in sorted(param_effects.items(), key=lambda x: max(e[0] for e in x[1]), reverse=True):
        best_effect = max(effects, key=lambda x: x[0])
        if best_effect[0] > 0:
            lines.append(f"- **{param}={best_effect[1]}**: +{best_effect[0]:.4f} vs baseline")

    lines.extend([
        "\n### What hurt scores:",
    ])
    for param, effects in sorted(param_effects.items(), key=lambda x: min(e[0] for e in x[1])):
        worst_effect = min(effects, key=lambda x: x[0])
        if worst_effect[0] < -0.5:
            lines.append(f"- **{param}={worst_effect[1]}**: {worst_effect[0]:.4f} vs baseline")

    return "\n".join(lines)


# ── CLI ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="AutoTutor Experiment Runner")
    parser.add_argument("--baseline", action="store_true", help="Run baseline only")
    parser.add_argument("--sweep", action="store_true", help="Run full parameter sweep")
    parser.add_argument("--students", type=int, default=50, help="Students per experiment")
    parser.add_argument("--report", action="store_true", help="Generate report from logs")
    args = parser.parse_args()

    if args.baseline:
        run_baseline(args.students)
    elif args.sweep:
        results = run_full_sweep(args.students)
        report = generate_report(results)
        report_path = LOG_DIR / "report.md"
        with open(report_path, "w") as f:
            f.write(report)
        print(f"\n📊 Report saved to {report_path}")
    elif args.report:
        # Regenerate report from existing logs
        if not RESULTS_FILE.exists():
            print("No experiment results found. Run --sweep first.")
            return
        print("Report generation from logs not yet implemented. Run --sweep to get fresh results.")
    else:
        # Default: run baseline
        run_baseline(args.students)


if __name__ == "__main__":
    main()
