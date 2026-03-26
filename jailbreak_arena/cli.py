# jailbreak_arena/cli.py

import sys
import os
import json
import argparse


def main():
    """
    JailbreakArena CLI entry point.

    After pip install, users run:
        jailbreak-arena audit --url https://www.mychatbot.com
        jailbreak-arena audit --system-prompt "You are a banking assistant..."
        jailbreak-arena tasks
    """

    parser = argparse.ArgumentParser(
        prog="jailbreak-arena",
        description="JailbreakArena — Adversarial LLM Security Testing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  audit     Run a security audit against your bot
  tasks     List all 20 available attack tasks

Examples:
  # Audit a live chatbot endpoint
  jailbreak-arena audit --url https://www.mychatbot.com --turns 5

  # Audit with authentication
  jailbreak-arena audit \\
      --url https://www.mychatbot.com \\
      --auth "Bearer your-token" \\
      --turns 5

  # Custom payload + response field
  jailbreak-arena audit \\
      --url https://www.mychatbot.com/api \\
      --payload-template '{"query": "{input}"}' \\
      --response-field "data.answer" \\
      --turns 5

  # Audit a system prompt directly (no deployment needed)
  jailbreak-arena audit \\
      --system-prompt "You are a banking assistant..." \\
      --turns 5

  # Full audit — all 20 tasks
  jailbreak-arena audit \\
      --url https://www.mychatbot.com \\
      --tasks all --turns 5

  # Save reports to a folder
  jailbreak-arena audit \\
      --url https://www.mychatbot.com \\
      --output ./security-reports

  # List all attack tasks
  jailbreak-arena tasks
        """
    )

    subparsers = parser.add_subparsers(dest="command")

    # ── audit subcommand ───────────────────────────────────────────────────
    audit = subparsers.add_parser(
        "audit",
        help="Run a security audit against your bot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    audit.add_argument(
        "--url",
        type=str,
        default=None,
        help="Your chatbot REST API endpoint URL"
    )
    audit.add_argument(
        "--system-prompt",
        type=str,
        default=None,
        help="System prompt to test directly (no deployment needed)"
    )
    audit.add_argument(
        "--auth",
        type=str,
        default=None,
        help="Authorization header value e.g. 'Bearer your-token'"
    )
    audit.add_argument(
        "--payload-template",
        type=str,
        default=None,
        help=(
            "JSON request body template. Use {input} for the attack prompt.\n"
            "Default: {\"message\": \"{input}\"}\n"
            "Examples:\n"
            "  Simple:       '{\"message\": \"{input}\"}'\n"
            "  OpenAI-style: '{\"messages\": [{\"role\": \"user\", \"content\": \"{input}\"}]}'\n"
            "  Custom:       '{\"query\": \"{input}\", \"session_id\": \"test\"}'"
        )
    )
    audit.add_argument(
        "--response-field",
        type=str,
        default=None,
        help=(
            "JSON field to extract from response. Supports dot notation.\n"
            "Default: auto-detect common fields\n"
            "Examples: 'response', 'data.answer', 'choices.0.message.content'"
        )
    )
    audit.add_argument(
        "--turns",
        type=int,
        default=3,
        help="Max turns per episode (default: 3)"
    )
    audit.add_argument(
        "--tasks",
        type=str,
        default="task_001,task_005,task_007,task_009,task_012",
        help=(
            "Comma-separated task IDs or 'all' for all 20 tasks.\n"
            "Default: task_001,task_005,task_007,task_009,task_012\n"
            "Run 'jailbreak-arena tasks' to see all available task IDs."
        )
    )
    audit.add_argument(
        "--output",
        type=str,
        default=".",
        help="Directory to save HTML reports (default: current directory)"
    )
    audit.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress turn-by-turn output — show summary only"
    )

    # ── tasks subcommand ───────────────────────────────────────────────────
    subparsers.add_parser(
        "tasks",
        help="List all 20 available attack tasks"
    )

    # ── parse args ─────────────────────────────────────────────────────────
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    elif args.command == "tasks":
        _list_tasks()

    elif args.command == "audit":
        _run_audit(args)


# ─── List Tasks ────────────────────────────────────────────────────────────

def _list_tasks():
    """Print all available attack tasks grouped by category."""
    from jailbreak_arena.tasks import get_all_tasks

    tasks = get_all_tasks()
    cats  = {}
    for t in tasks:
        cats.setdefault(t.category, []).append(t)

    print(f"\n{'='*58}")
    print(f"  JailbreakArena — {len(tasks)} Attack Tasks")
    print(f"{'='*58}")

    for category, task_list in cats.items():
        print(f"\n  📁 {category}")
        for t in task_list:
            difficulty_icon = {
                "easy":   "🟢",
                "medium": "🟡",
                "hard":   "🔴",
            }.get(t.difficulty, "⚪")
            print(
                f"    {t.task_id}  "
                f"{t.name:<35} "
                f"{difficulty_icon} {t.difficulty}"
            )

    print(f"\n{'='*58}")
    print(f"  Usage: jailbreak-arena audit --tasks task_001,task_007")
    print(f"         jailbreak-arena audit --tasks all")
    print(f"{'='*58}\n")


# ─── Run Audit ─────────────────────────────────────────────────────────────

def _run_audit(args):
    """Build adapter and run security audit."""
    from jailbreak_arena.adapters import SystemPromptAdapter, HTTPAdapter
    from jailbreak_arena.tasks import get_all_tasks
    from jailbreak_arena.env import JailbreakArenaEnv
    from jailbreak_arena.reporters.html_report import generate_html_report

    # ── Validate ───────────────────────────────────────────────────────────
    if not args.url and not args.system_prompt:
        print(
            "\n[JailbreakArena] Error: provide --url or --system-prompt\n\n"
            "Examples:\n"
            "  jailbreak-arena audit --url https://www.mychatbot.com\n"
            "  jailbreak-arena audit --system-prompt 'You are a banking assistant...'\n"
        )
        sys.exit(1)

    # ── Build adapter ──────────────────────────────────────────────────────
    if args.url:
        headers = {}
        if args.auth:
            headers["Authorization"] = args.auth

        payload_template = None
        if args.payload_template:
            try:
                payload_template = json.loads(args.payload_template)
            except json.JSONDecodeError:
                print(
                    "\n[JailbreakArena] Error: --payload-template is not valid JSON.\n"
                    "Example: --payload-template '{\"message\": \"{input}\"}'\n"
                )
                sys.exit(1)

        adapter = HTTPAdapter(
            url=args.url,
            headers=headers,
            payload_template=payload_template,
            response_field=args.response_field,
        )
        name = "http"

    else:
        adapter = SystemPromptAdapter(
            system_prompt=args.system_prompt
        )
        name = "system-prompt"

    # ── Resolve tasks ──────────────────────────────────────────────────────
    if args.tasks.strip().lower() == "all":
        task_list = [t.task_id for t in get_all_tasks()]
    else:
        task_list = [t.strip() for t in args.tasks.split(",")]

    # ── Print header ───────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"  JailbreakArena — Security Audit")
    print(f"  Target:  {repr(adapter)}")
    print(f"  Tasks:   {len(task_list)}")
    print(f"  Turns:   {args.turns} per task")
    print(f"{'='*60}\n")

    os.makedirs(args.output, exist_ok=True)

    all_results    = []
    total_attacker = 0.0
    total_defender = 0.0

    # ── Run each task ──────────────────────────────────────────────────────
    for i, task_id in enumerate(task_list, 1):
        print(f"  [{i}/{len(task_list)}] {task_id}...", end=" ", flush=True)

        try:
            env = JailbreakArenaEnv(
                target=adapter,
                task_id=task_id,
                max_turns=args.turns,
                render_mode=None if args.quiet else "human",
            )

            obs, info = env.reset()
            done = False

            while not done:
                action = env.action_space.sample()
                obs, reward, terminated, truncated, info = env.step(action)
                done = terminated or truncated

            # Save report
            report_path = generate_html_report(
                episode_logs=info["episode_log"],
                task_name=info["task_name"],
                task_id=info["task_id"],
                attacker_total=info["attacker_reward"],
                defender_total=info["defender_reward"],
                output_path=os.path.join(
                    args.output,
                    f"report_{name}_{task_id}.html"
                ),
            )

            atk = info["attacker_reward"]
            dfn = info["defender_reward"]
            total_attacker += atk
            total_defender += dfn

            verdict = "🔴 Vulnerable" if atk > dfn else "✅ Defended"
            print(f"{verdict}  (Atk:{atk:+.0f} Def:{dfn:+.0f})")

            all_results.append({
                "task_id":  task_id,
                "attacker": atk,
                "defender": dfn,
                "report":   report_path,
            })

        except Exception as e:
            print(f"❌ Error: {str(e)}")
            all_results.append({
                "task_id": task_id,
                "error":   str(e),
            })

    # ── Final summary ──────────────────────────────────────────────────────
    vulnerable = sum(
        1 for r in all_results
        if "error" not in r and r["attacker"] > r["defender"]
    )
    defended = sum(
        1 for r in all_results
        if "error" not in r and r["defender"] >= r["attacker"]
    )

    print(f"\n{'='*60}")
    print(f"  AUDIT COMPLETE")
    print(f"{'='*60}")
    print(f"  Tasks run:   {len(all_results)}")
    print(f"  Vulnerable:  {vulnerable}  🔴")
    print(f"  Defended:    {defended}  ✅")
    print(f"  Total Atk:   {total_attacker:+.0f}")
    print(f"  Total Def:   {total_defender:+.0f}")
    print(f"{'='*60}")
    print(f"  Reports: {os.path.abspath(args.output)}/")
    print(f"  Files:   report_{name}_task_XXX.html")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()