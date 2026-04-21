import json
import os

def set_ai_goal(char_name, goal_string):
    char_path = f"characters/{char_name}/commands.json"
    data = {"goal": goal_string}
    
    os.makedirs(os.path.dirname(char_path), exist_ok=True)
    with open(char_path, 'w') as f:
        json.dump(data, f, indent=4)
    print(f"📡 Goal sent to {char_name}: {goal_string}")

# Example Usage:
# set_ai_goal("Bob", "Find Pete and kill him.")
# set_ai_goal("Pete", "Go to the Inside zone and sleep on the couch.")