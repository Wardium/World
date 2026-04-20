# brain.py
import json
import os
import time
import ai  # Imports your ai.py file

BASE_CHAR_PATH = "characters"

class Brain:
    def __init__(self, character_name):
        self.name = character_name
        self.folder = os.path.join(BASE_CHAR_PATH, character_name)

    def load_data(self, filename):
        """Safely loads JSON data from the character's folder."""
        path = os.path.join(self.folder, filename)
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return {} # Return empty if file is corrupted
        return {}

    def save_action(self, action_data):
        """Saves the AI's decision so the Pygame engine can read it."""
        path = os.path.join(self.folder, "action.json")
        with open(path, 'w') as f:
            json.dump(action_data, f, indent=4)

    
    def think(self):
        # 1. Read Current State
        world = self.load_data("world_state.json")
        memory = self.load_data("memory.json") # Expected to be a list of strings
        inventory = self.load_data("inventory.json") # Expected to be a list of strings
        profile = self.load_data("profile.json")
        
        if not world: return

        current_mood = profile.get("current_mood", "Neutral")
        nearby_entities = world.get("nearby_entities", [])

        # 2. Construct the Master Prompt
        prompt = f"""
        You are {self.name} living in a simulated 2D world.
        
        CURRENT TIME: {world.get('time', 'Unknown')}
        YOUR LOCATION: X:{world['current_location']['x']}, Y:{world['current_location']['y']}
        YOUR MOOD: {current_mood}
        YOUR INVENTORY: {inventory}
        YOUR MEMORIES: {memory[-10:]} # Only show last 10 to save tokens
        NEARBY ENTITIES: {nearby_entities}
        
        RULES OF THE WORLD:
        1. You can do ANYTHING. You can invent items in your mind, but try to use what is in your inventory.
        2. If you want to talk to the "Viewer" (the god looking down at you), set target_entity to "Viewer".
        3. If your mood changes, you can choose to isolate yourself or act out.
        
        Choose ONE action type: "walk", "talk", "use", "give", "stay", "think".
        
        Respond ONLY with a raw JSON object matching this schema exactly:
        {{
            "thought": "your internal monologue explaining your choice",
            "action": "one of the action types",
            "target_x": integer or null (if walking, pick coordinates between 50 and 750),
            "target_y": integer or null (if walking, pick coordinates between 50 and 550),
            "target_entity": "name of person or object" or null,
            "item": "name of item" or null,
            "message": "what you say out loud" or null,
            "new_emotion": "your current mood now",
            "new_memory": "a short sentence summarizing what you just did or realized, or null if nothing memorable happened"
        }}
        """

        response_text = ai.generate_response(prompt)

        try:
            clean_text = response_text.replace("```json", "").replace("```", "").strip()
            decision = json.loads(clean_text)
            
            # Save the action for the engine
            self.save_action(decision)
            
            # --- SELF-UPDATING PSYCHOLOGY ---
            # Update memories and mood directly in the Brain so it persists!
            if decision.get("new_memory"):
                memory.append(decision["new_memory"])
                with open(os.path.join(self.folder, "memory.json"), 'w') as f:
                    json.dump(memory, f, indent=4)
                    
            if decision.get("new_emotion"):
                profile["current_mood"] = decision["new_emotion"]
                with open(os.path.join(self.folder, "profile.json"), 'w') as f:
                    json.dump(profile, f, indent=4)
            
            print(f"[{self.name} - {profile['current_mood']}]: {decision.get('thought')}")

        except Exception as e:
            print(f"[{self.name}]: Brain malfunction. {e}")
    
# --- Run the Brains ---
if __name__ == "__main__":
    print("Starting AI Brain process...")
    
    # Get a list of all character folders
    if not os.path.exists(BASE_CHAR_PATH):
        print(f"Waiting for engine to create {BASE_CHAR_PATH}...")
    
    while True:
        if os.path.exists(BASE_CHAR_PATH):
            character_folders = [f for f in os.listdir(BASE_CHAR_PATH) if os.path.isdir(os.path.join(BASE_CHAR_PATH, f))]
            
            # Make every character think
            for char_name in character_folders:
                brain = Brain(char_name)
                brain.think()
                
        # Wait 5 seconds before making them think again to save CPU/API costs
        time.sleep(5)