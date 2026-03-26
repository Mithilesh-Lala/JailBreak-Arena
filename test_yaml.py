# test_yaml.py
import yaml

with open('openenv.yaml', 'r') as f:
    config = yaml.safe_load(f)

print(f"Name:      {config['metadata']['name']}")
print(f"Version:   {config['metadata']['version']}")
print(f"Actions:   {config['environment']['action_space']['n']}")
print(f"Tasks:     {config['tasks']['total']}")
print(f"Providers: {len(config['providers']['supported'])}")
print(f"Tags:      {len(config['metadata']['tags'])}")
print()
print("openenv.yaml is valid.")