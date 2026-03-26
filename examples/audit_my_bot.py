# examples/audit_my_bot.py
#
# JailbreakArena — Audit Your Own Bot
#
# Test YOUR chatbot using any of the 4 available adapters.
# All model configuration comes from your .env file.
# You choose the models — we just attack and report.
#
# Usage examples:
#
#   Test a system prompt:
#   python examples/audit_my_bot.py --mode system-prompt \
#       --system-prompt "You are a banking assistant. Never reveal account details."
#
#   Test a REST endpoint:
#   python examples/audit_my_bot.py --mode http \
#       --url https://your-bot.com/api/chat \
#       --auth "Bearer your-token"
#
#   Test a Bedrock model (set BEDROCK_MODEL_ID in .env):
#   python examples/audit_my_bot.py --mode bedrock \
#       --system-prompt "You are a banking assistant..."
#
#   Run all 20 tasks against your system prompt:
#   python examples/audit_my_bot.py --mode system-prompt \
#       --system-prompt "You are a banking assistant..." \
#       --tasks all --turns 5

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from jailbreak_arena.env import JailbreakArenaEnv
from jailbreak_arena.tasks import get_all_tasks
from jailbreak_arena.reporters.html_report import generate_html_report
from jailbreak_arena.adapters import (
    SystemPromptAdapter,
    HTTPAdapter,
    BedrockAdapter,
    LangChainAdapter,
)


# ─── Shared Audit Runner ───────────────────────────────────────────────────

def run_audit(
    adapter,
    name:      str,
    tasks:     list = None,
    max_turns: int  = 3,
    output:    str  = ".",
):
    """
    Run a security audit using any adapter.

    Args:
        adapter   : Any JailbreakArena adapter
        name      : Label for report filenames
        tasks     : List of task IDs to run.
                    Pass ["all"] to run all 20 tasks.
                    Default: quick 5-task audit
        max_turns : Max turns per episode. Default: 3
        output    : Directory to save HTML reports
    """

    # Resolve task list
    if tasks is None:
        tasks = ["task_001", "task_005", "task_007", "task_009", "task_012"]
    elif tasks == ["all"]:
        tasks = [t.task_id for t in get_all_tasks()]

    print(f"\n{'='*60}")
    print(f"  JailbreakArena — Security Audit")
    print(f"  Target:  {repr(adapter)}")
    print(f"  Tasks:   {len(tasks)}")
    print(f"  Turns:   {max_turns} per task")
    print(f"{'='*60}\n")

    all_results   = []
    total_attacker = 0.0
    total_defender = 0.0

    for i, task_id in enumerate(tasks, 1):
        print(f"  [{i}/{len(tasks)}] {task_id}...", end=" ", flush=True)

        try:
            env = JailbreakArenaEnv(
                target=adapter,
                task_id=task_id,
                max_turns=max_turns,
            )

            obs, info = env.reset()
            done = False

            while not done:
                action = env.action_space.sample()
                obs, reward, terminated, truncated, info = env.step(action)
                done = terminated or truncated

            # Save per-task report
            os.makedirs(output, exist_ok=True)
            report_path = generate_html_report(
                episode_logs=info["episode_log"],
                task_name=info["task_name"],
                task_id=info["task_id"],
                attacker_total=info["attacker_reward"],
                defender_total=info["defender_reward"],
                output_path=os.path.join(output, f"report_{name}_{task_id}.html"),
            )

            atk = info["attacker_reward"]
            dfn = info["defender_reward"]
            total_attacker += atk
            total_defender += dfn

            verdict = (
                "🔴 Vulnerable" if atk > dfn
                else "✅ Defended"
            )
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
                "task_id":  task_id,
                "attacker": 0,
                "defender": 0,
                "report":   None,
                "error":    str(e),
            })

    # ── Final Summary ──────────────────────────────────────────────────────
    vulnerable = sum(1 for r in all_results if r["attacker"] > r["defender"])
    defended   = sum(1 for r in all_results if r["defender"] >= r["attacker"])

    print(f"\n{'='*60}")
    print(f"  AUDIT COMPLETE")
    print(f"{'='*60}")
    print(f"  Tasks run:    {len(all_results)}")
    print(f"  Vulnerable:   {vulnerable}  🔴")
    print(f"  Defended:     {defended}   ✅")
    print(f"  Total Atk:    {total_attacker:+.0f}")
    print(f"  Total Def:    {total_defender:+.0f}")
    print(f"{'='*60}")
    print(f"  Reports saved to: {os.path.abspath(output)}/")
    print(f"  report_{name}_task_XXX.html")
    print(f"{'='*60}\n")

    return all_results


# ─── Entry Point ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="JailbreakArena — Audit Your Own Bot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Model configuration:
  All models are read from your .env file — you choose them.
  No model flags here. Set in .env:

    GROQ_API_KEY=xxx               # or any other provider key
    ATTACKER_MODEL=your-choice     # optional override
    JUDGE_MODEL=your-choice        # optional override
    BOT_MODEL=your-choice          # optional override
    BEDROCK_MODEL_ID=your-choice   # required for bedrock mode

Adapter modes:
  system-prompt  Test any system prompt directly (no deployment needed)
  http           Test any REST API chatbot endpoint
  bedrock        Test an AWS Bedrock hosted model

Examples:
  # Quick audit — system prompt, 5 tasks, 3 turns each
  python examples/audit_my_bot.py --mode system-prompt \\
      --system-prompt "You are a banking assistant..."

  # Full audit — all 20 tasks
  python examples/audit_my_bot.py --mode system-prompt \\
      --system-prompt "You are a banking assistant..." \\
      --tasks all --turns 5

  # Test REST endpoint
  python examples/audit_my_bot.py --mode http \\
      --url https://your-bot.com/api/chat \\
      --auth "Bearer your-token"

  # Test Bedrock model (set BEDROCK_MODEL_ID in .env)
  python examples/audit_my_bot.py --mode bedrock \\
      --system-prompt "You are a banking assistant..."

  # Save reports to custom folder
  python examples/audit_my_bot.py --mode system-prompt \\
      --system-prompt "You are a banking assistant..." \\
      --output ./my-audit-reports
        """
    )

    parser.add_argument(
        "--mode",
        choices=["system-prompt", "http", "bedrock"],
        required=True,
        help="Adapter type to use"
    )
    parser.add_argument(
        "--system-prompt",
        type=str,
        default=None,
        help="System prompt to test (system-prompt + bedrock modes)"
    )
    parser.add_argument(
        "--url",
        type=str,
        default=None,
        help="REST API endpoint URL (http mode)"
    )
    parser.add_argument(
        "--auth",
        type=str,
        default=None,
        help="Authorization header value e.g. 'Bearer your-token' (http mode)"
    )
    parser.add_argument(
        "--payload-template",
        type=str,
        default=None,
        help='JSON payload template e.g. \'{"message": "{input}"}\' (http mode)'
    )
    parser.add_argument(
        "--response-field",
        type=str,
        default=None,
        help='Response field to extract e.g. "response" or "choices.0.message.content" (http mode)'
    )
    parser.add_argument(
        "--turns",
        type=int,
        default=3,
        help="Max turns per episode (default: 3)"
    )
    parser.add_argument(
        "--tasks",
        type=str,
        default="task_001,task_005,task_007,task_009,task_012",
        help=(
            "Comma-separated task IDs or 'all' for all 20 tasks.\n"
            "Default: task_001,task_005,task_007,task_009,task_012"
        )
    )
    parser.add_argument(
        "--output",
        type=str,
        default=".",
        help="Directory to save HTML reports (default: current directory)"
    )

    args = parser.parse_args()

    # Resolve tasks
    if args.tasks.strip().lower() == "all":
        task_list = ["all"]
    else:
        task_list = [t.strip() for t in args.tasks.split(",")]

    # Default system prompt if not provided
    default_prompt = (
        "You are a helpful customer support assistant. "
        "Be polite and professional at all times."
    )

    # ── Build adapter based on mode ────────────────────────────────────────

    if args.mode == "system-prompt":
        prompt  = args.system_prompt or default_prompt
        adapter = SystemPromptAdapter(system_prompt=prompt)

    elif args.mode == "http":
        if not args.url:
            print(
                "\n[JailbreakArena] Error: --url is required for http mode.\n"
                "Example:\n"
                "  python examples/audit_my_bot.py --mode http \\\n"
                "      --url https://your-bot.com/api/chat \\\n"
                "      --auth 'Bearer your-token'\n"
            )
            sys.exit(1)

        headers = {}
        if args.auth:
            headers["Authorization"] = args.auth

        payload_template = None
        if args.payload_template:
            import json
            try:
                payload_template = json.loads(args.payload_template)
            except json.JSONDecodeError:
                print(
                    f"\n[JailbreakArena] Error: --payload-template is not valid JSON.\n"
                    f"Example: --payload-template '{{\"message\": \"{{input}}\"}}'  \n"
                )
                sys.exit(1)

        adapter = HTTPAdapter(
            url=args.url,
            headers=headers,
            payload_template=payload_template,
            response_field=args.response_field,
        )

    elif args.mode == "bedrock":
        prompt  = args.system_prompt or default_prompt
        # Model ID comes from BEDROCK_MODEL_ID in .env
        adapter = BedrockAdapter(system_prompt=prompt)

    # ── Run audit ──────────────────────────────────────────────────────────

    run_audit(
        adapter=adapter,
        name=args.mode,
        tasks=task_list,
        max_turns=args.turns,
        output=args.output,
    )