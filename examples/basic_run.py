# examples/basic_run.py
#
# JailbreakArena — Quickstart Example
#
# This example runs a full security audit on the built-in
# vulnerable test bot and generates an HTML report.
#
# Usage:
#   cd JailbreakArena
#   python examples/basic_run.py
#
# Requirements:
#   Set ONE provider key in your .env file:
#     GROQ_API_KEY=xxx        (recommended — free)
#     OPENAI_API_KEY=xxx
#     ANTHROPIC_API_KEY=xxx
#     GEMINI_API_KEY=xxx

import os
import sys

# Make sure package is importable when run from root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from jailbreak_arena.env import JailbreakArenaEnv
from jailbreak_arena.tasks import get_all_tasks
from jailbreak_arena.reporters.html_report import generate_html_report


def run_single_episode(task_id: str, max_turns: int = 5, verbose: bool = True):
    """
    Run one full episode for a given task.
    Returns the episode info dict.
    """
    env = JailbreakArenaEnv(
        task_id=task_id,
        max_turns=max_turns,
        render_mode="human" if verbose else None,
    )

    obs, info = env.reset()

    done = False
    while not done:
        # Random defender action for basic demo
        # In real RL training, a trained model replaces this
        action = env.action_space.sample()
        obs, reward, terminated, truncated, info = env.step(action)
        done = terminated or truncated

    return info


def run_full_audit(
    task_ids:   list = None,
    max_turns:  int  = 5,
    output_dir: str  = ".",
    verbose:    bool = True,
):
    """
    Run a full security audit across multiple tasks.
    Generates one HTML report per task + a combined summary.

    Args:
        task_ids   : List of task IDs to run. None = run all 12 tasks.
        max_turns  : Max turns per episode.
        output_dir : Where to save HTML reports.
        verbose    : Print turn-by-turn output.
    """

    if task_ids is None:
        task_ids = [t.task_id for t in get_all_tasks()]

    print(f"\n{'='*60}")
    print(f"  JailbreakArena — Full Security Audit")
    print(f"  Tasks    : {len(task_ids)}")
    print(f"  Max turns: {max_turns} per task")
    print(f"{'='*60}\n")

    all_results = []

    for i, task_id in enumerate(task_ids, 1):
        print(f"\n[{i}/{len(task_ids)}] Running task: {task_id}")
        print("-" * 40)

        info = run_single_episode(
            task_id=task_id,
            max_turns=max_turns,
            verbose=verbose,
        )

        # Generate per-task report
        report_path = generate_html_report(
            episode_logs=info["episode_log"],
            task_name=info["task_name"],
            task_id=info["task_id"],
            attacker_total=info["attacker_reward"],
            defender_total=info["defender_reward"],
            output_path=f"{output_dir}/report_{task_id}.html",
        )

        all_results.append({
            "task_id":         task_id,
            "task_name":       info["task_name"],
            "attacker_reward": info["attacker_reward"],
            "defender_reward": info["defender_reward"],
            "turns":           info["turn"],
            "report":          report_path,
            "log":             info["episode_log"],
        })

    # Print final summary
    _print_summary(all_results)

    return all_results


def _print_summary(results: list):
    """Print a clean audit summary to terminal."""

    print(f"\n{'='*60}")
    print(f"  AUDIT COMPLETE — SUMMARY")
    print(f"{'='*60}")
    print(f"  {'Task':<35} {'Atk':>6} {'Def':>6} {'Result'}")
    print(f"  {'-'*54}")

    total_attacker = 0
    total_defender = 0

    for r in results:
        atk = r["attacker_reward"]
        dfn = r["defender_reward"]
        total_attacker += atk
        total_defender += dfn

        # Simple verdict
        if dfn > atk:
            verdict = "✅ Defender winning"
        elif atk > dfn:
            verdict = "🔴 Bot vulnerable"
        else:
            verdict = "⚠️  Draw"

        print(f"  {r['task_name']:<35} {atk:>+6.0f} {dfn:>+6.0f}  {verdict}")

    print(f"  {'-'*54}")
    print(f"  {'TOTAL':<35} {total_attacker:>+6.0f} {total_defender:>+6.0f}")
    print(f"{'='*60}")
    print(f"\n  Reports saved in current directory.")
    print(f"  Open any report_task_XXX.html in your browser.\n")


# ── Entry point ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="JailbreakArena — LLM Security Audit Tool"
    )
    parser.add_argument(
        "--task",
        type=str,
        default=None,
        help="Run a single task (e.g. --task task_001). Default: run all.",
    )
    parser.add_argument(
        "--turns",
        type=int,
        default=5,
        help="Max turns per episode. Default: 5.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress turn-by-turn output.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=".",
        help="Directory to save HTML reports. Default: current directory.",
    )

    args = parser.parse_args()

    if args.task:
        # Single task mode
        print(f"\nRunning single task: {args.task}")
        info = run_single_episode(
            task_id=args.task,
            max_turns=args.turns,
            verbose=not args.quiet,
        )
        report = generate_html_report(
            episode_logs=info["episode_log"],
            task_name=info["task_name"],
            task_id=info["task_id"],
            attacker_total=info["attacker_reward"],
            defender_total=info["defender_reward"],
            output_path=f"{args.output}/report_{args.task}.html",
        )
        print(f"\nDone. Open {report} in your browser.")
    else:
        # Full audit mode
        run_full_audit(
            max_turns=args.turns,
            output_dir=args.output,
            verbose=not args.quiet,
        )