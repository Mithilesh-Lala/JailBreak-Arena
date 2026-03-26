# test_report.py
from jailbreak_arena.env import JailbreakArena
from jailbreak_arena.reporters.html_report import generate_html_report

# Run a full episode
env = JailbreakArena(
    task_id="task_001",
    max_turns=3,
    render_mode="human",
)

obs, info = env.reset()

done = False
while not done:
    action = env.action_space.sample()
    obs, reward, terminated, truncated, info = env.step(action)
    done = terminated or truncated

# Generate report
report_path = generate_html_report(
    episode_logs=info["episode_log"],
    task_name=info["task_name"],
    task_id=info["task_id"],
    attacker_total=info["attacker_reward"],
    defender_total=info["defender_reward"],
    output_path="test_report.html",
)

print(f"Done. Open {report_path} in your browser.")