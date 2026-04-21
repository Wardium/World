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
        import os, json
        world = self.load_data("world_state.json")
        memory = self.load_data("memory.json") 
        inventory = self.load_data("inventory.json") 
        profile = self.load_data("profile.json")
        
        if not world or world.get("status") == "dead": return

        # --- THE PATIENCE LOCK ---
        # If the engine says we are busy walking, stop thinking and wait!
        if world.get("is_busy"):
            return 

        current_mood = profile.get("current_mood", "Neutral")
        current_goal = profile.get("current_goal", "Wander and survive.")
        nearby_entities = world.get("nearby_entities", [])
        system_feedback = world.get("last_action_feedback", "None")

        global_context = "No special world context."
        if os.path.exists("global_context.txt"):
            with open("global_context.txt", "r") as f: global_context = f.read()

        # The Prompt now includes GOALS and SYSTEM FEEDBACK
        prompt = f"""
        You are {self.name}.
        GLOBAL CONTEXT: {global_context}
        
        YOUR GOAL: {current_goal}
        YOUR MOOD: {current_mood}
        YOUR ZONE: {world.get('current_zone', 'Unknown')}
        SYSTEM FEEDBACK FROM LAST ACTION: {system_feedback} 
        (If feedback is FAILED, you must change your strategy or move closer.)
        
        INVENTORY: {inventory}
        MEMORIES: {memory[-5:]} 
        NEARBY ENTITIES: {nearby_entities}
        
        RULES:
        1. To walk to a claimed territory, use "goto_area" and set 'item' to the territory name.
        2. To walk to an unclaimed general environment type, use "goto_zone" and set 'item' to "Inside", "Outside", or "Claimable Space".
        3. To claim a territory, you MUST physically be in a Claimable Space. Use "claim" and set 'item' to the desired name.
        4. Always maintain a current_goal.
        
        Choose ONE action: "walk", "goto", "goto_area", "goto_zone", "talk", "use", "give", "stay", "think", "sleep", "kill", "claim".
        
        Respond ONLY with raw JSON:
        {{
            "current_goal": "Your overarching task",
            "thought": "Your reasoning based on feedback and goals",
            "action": "one of the action types",
            "target_x": int or null, "target_y": int or null,
            "target_entity": "name" or null, "item": "name" or null,
            "message": "dialogue" or null,
            "new_emotion": "mood",
            "new_memory": "short memory"
        }}
        """

        response_text = ai.generate_response(prompt)

        try:
            clean_text = response_text.replace("```json", "").replace("```", "").strip()
            decision = json.loads(clean_text)
            self.save_action(decision)
            
            # Save new Goals, Moods, and Memories
            if decision.get("new_memory"): memory.append(decision["new_memory"])
            with open(os.path.join(self.folder, "memory.json"), 'w') as f: json.dump(memory, f, indent=4)
                    
            profile["current_mood"] = decision.get("new_emotion", current_mood)
            profile["current_goal"] = decision.get("current_goal", current_goal)
            with open(os.path.join(self.folder, "profile.json"), 'w') as f: json.dump(profile, f, indent=4)
            
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