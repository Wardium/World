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
        """The core loop for gathering data, prompting the AI, and acting."""
        
        # 1. Read Current State
        world = self.load_data("world_state.json")
        memory = self.load_data("memory.json")
        inventory = self.load_data("inventory.json")
        goals = self.load_data("goals.json")
        
        # If the engine hasn't written the world state yet, skip thinking
        if not world:
            return

        # 2. Construct the Prompt for the AI
        prompt = f"""
        You are {self.name} living in a simulated world.
        
        CURRENT TIME: {world.get('time', 'Unknown')}
        YOUR LOCATION: {world.get('current_location', 'Unknown')}
        
        YOUR INVENTORY: {inventory}
        YOUR GOALS/EMOTIONS: {goals}
        YOUR MEMORIES: {memory}
        
        Based on this information, what do you want to do right now?
        Choose a target destination from: ["HOME", "WORK", "STORE"]
        
        You must respond ONLY in valid JSON format like this example:
        {{"target_poi": "WORK", "current_thought": "I am feeling poor, I need to work."}}
        """

        # 3. Send to the AI Wrapper
        response_text = ai.generate_response(prompt)

        # 4. Parse the AI's Output and execute the action
        try:
            # Clean up the text in case the AI added Markdown formatting like ```json
            clean_text = response_text.replace("```json", "").replace("```", "").strip()
            decision = json.loads(clean_text)
            
            # Save it for the engine
            self.save_action(decision)
            
            print(f"[{self.name}]: {decision.get('current_thought')}")
            print(f"   -> Heading to: {decision.get('target_poi')}\n")

        except json.JSONDecodeError:
            print(f"[{self.name}]: Brain malfunction. AI did not return valid JSON.")

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