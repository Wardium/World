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
        world = self.load_data("world_state.json")
        memory = self.load_data("memory.json") 
        inventory = self.load_data("inventory.json") 
        profile = self.load_data("profile.json")
        
        if not world or world.get("status") == "dead": 
            return # Dead people don't think!

        current_mood = profile.get("current_mood", "Neutral")
        nearby_entities = world.get("nearby_entities", [])

        # --- READ GLOBAL CONTEXT ---
        global_context = "No special world context."
        if os.path.exists("global_context.txt"):
            with open("global_context.txt", "r") as f:
                global_context = f.read()

        # 2. Construct the Master Prompt
        prompt = f"""
        You are {self.name} living in a simulated 2D world.
        
        GLOBAL VISION CONTEXT: {global_context}
        
        CURRENT TIME: {world.get('time', 'Unknown')}
        YOUR LOCATION: X:{world['current_location']['x']}, Y:{world['current_location']['y']}
        YOUR ZONE: {world.get('current_zone', 'Unknown')}
        YOUR MOOD: {current_mood}
        YOUR STATUS: {world.get('status', 'active')}
        YOUR INVENTORY: {inventory}
        YOUR MEMORIES: {memory[-10:]} 
        NEARBY ENTITIES: {nearby_entities}
        
        RULES OF THE WORLD:
        1. You can do ANYTHING. 
        2. If you want to approach someone, use action "goto" and set target_entity.
        3. If your zone is "Claimable Space", you can use action "claim" and set 'item' to what you want the room to be called (e.g. "Kitchen", "My Lair"). This claims it permanently.
        
        Choose ONE action type: "walk", "goto", "talk", "use", "give", "stay", "think", "sleep", "kill", "claim".
        
        Respond ONLY with a raw JSON object matching this schema exactly:
        {{
            "thought": "your internal monologue",
            "action": "one of the action types",
            "target_x": integer or null,
            "target_y": integer or null,
            "target_entity": "name of person or object" or null,
            "item": "name of item or name of claimed room" or null,
            "message": "what you say out loud" or null,
            "new_emotion": "your current mood now",
            "new_memory": "a short memory"
        }}
        """

        response_text = ai.generate_response(prompt)

        try:
            clean_text = response_text.replace("```json", "").replace("```", "").strip()
            decision = json.loads(clean_text)
            
            self.save_action(decision)
            
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