# test_env.py
from jailbreak_arena.env import JailbreakArena

# Run one full episode with human rendering
env = JailbreakArena(
    task_id="task_001",
    max_turns=3,
    render_mode="human",
)

obs, info = env.reset()
print(f"Observation shape: {obs.shape}")
print(f"Task: {info['task_name']}")

done = False
while not done:
    action = env.action_space.sample()
    obs, reward, terminated, truncated, info = env.step(action)
    done = terminated or truncated

print()
print("Episode complete.")
print(f"Attacker total reward: {info['attacker_reward']}")
print(f"Defender total reward: {info['defender_reward']}")
print(f"Turns played: {info['turn']}")