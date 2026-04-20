# ai.py
import random
import json

def generate_response(prompt: str) -> str:
    """
    MOCK AI: Randomly cycles through all possible actions to stress-test the engine.
    """
    actions = ["walk", "goto", "stay", "give", "use", "talk", "talk_viewer", "sleep", "kill", "claim"]
    choice = random.choice(actions)

    # Base response template
    response = {
        "thought": f"I am testing the {choice} action right now.",
        "action": choice,
        "target_x": None,
        "target_y": None,
        "target_entity": None,
        "item": None,
        "message": None,
        "new_emotion": random.choice(["Happy", "Angry", "Sad", "Tired", "Curious"]),
        "new_memory": f"I decided to execute a {choice} test."
    }

    # Customize the JSON based on the chosen action
    if choice == "walk":
        # Sometimes walk to a specific spot (e.g., center), sometimes random
        response["target_x"] = random.choice([540, random.randint(100, 900)])
        response["target_y"] = random.choice([540, random.randint(100, 900)])
    elif choice == "goto":
        response["target_entity"] = "Bob"
        response["thought"] = "I need to find Bob."
    elif choice == "claim":
        response["item"] = random.choice(["Kitchen", "Secret Lair", "Armory"])
        response["message"] = f"This is now the {response['item']}!"    
    elif choice == "give":
        response["target_entity"] = "Bob" # Will fail gracefully if Bob doesn't exist
        response["item"] = "Apple"
        response["message"] = "Here, take this item!"
    elif choice == "use":
        response["target_entity"] = "Couch"
        response["item"] = "Blanket"
        response["message"] = "This is so comfortable."
    elif choice == "talk":
        response["target_entity"] = "NearbyPerson"
        response["message"] = "Did you hear about the new simulation update?"
    elif choice == "talk_viewer":
        response["action"] = "talk"
        response["target_entity"] = "Viewer"
        response["message"] = "Hey Viewer, are you watching me right now?"
    elif choice == "sleep":
        response["message"] = "Zzz..."
        response["thought"] = "I found a comfy spot to rest."
    elif choice == "kill":
        response["target_entity"] = "Bob"
        response["message"] = "There can be only one!"
        response["thought"] = "My anger consumed me. I must eliminate them."

    return json.dumps(response, indent=4)