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

    def recovery_logic(self, broken_text):
        """Attempts to extract at least the action and thought from a broken JSON string."""
        fallback = {"action": "stay", "thought": "I'm having trouble thinking clearly."}
        
        # Simple Regex to grab the action if it exists
        import re
        action_match = re.search(r'"action":\s*"(\w+)"', broken_text)
        if action_match:
            fallback["action"] = action_match.group(1)
            
        self.save_action(fallback)

    def think(self):
        import os, json
        
        clean_text = ""
        response_text = ""
        
        # 1. Load core files
        world = self.load_data("world_state.json")
        profile = self.load_data("profile.json")
        
        # --- NEW: COMMAND INJECTION ---
        external_command = None
        command_file = os.path.join(self.folder, "commands.json")
        
        if os.path.exists(command_file):
            cmd_data = self.load_data("commands.json")
            if cmd_data and "goal" in cmd_data:
                external_command = cmd_data["goal"]
                profile["current_goal"] = external_command
                os.remove(command_file) # Delete after reading so it doesn't get stuck!
        # ------------------------------
        
        # Force list-based files to actually be lists
        memory = self.load_data("memory.json") 
        if isinstance(memory, dict): memory = []
            
        inventory = self.load_data("inventory.json") 
        if isinstance(inventory, dict): inventory = []
            
        relationships = self.load_data("relationships.json") 
        if isinstance(relationships, dict): relationships = []
            
        chat_history = self.load_data("chat_history.json") 
        if isinstance(chat_history, dict): chat_history = []
        
        if not world or world.get("status") == "dead": return
        if world.get("is_busy"): return

        # 3. Gather Variables
        current_mood = profile.get("current_mood", "Neutral")
        current_goal = profile.get("current_goal", "Wander and survive.")
        bio = profile.get("bio", "You are a resident of this simulated world.")
        
        nearby_entities = world.get("nearby_entities", [])
        system_feedback = world.get("last_action_feedback", "None")

        global_context = "No special world context."
        if os.path.exists("global_context.txt"):
            with open("global_context.txt", "r") as f: global_context = f.read()

        goal_text = f"MASTER COMMAND: {external_command}" if external_command else current_goal

        # 4. Construct the Master Prompt
        prompt = f"""
        You are {self.name}. 
        YOUR PRIORITY GOAL: {goal_text}
        ABOUT YOU: {bio}
        
        CURRENT MOOD: {current_mood}
        CURRENT GOAL: {current_goal}
        
        WORLD CONTEXT: {global_context}
        YOUR ZONE: {world.get('current_zone', 'Unknown')}
        NEARBY ENTITIES & CONVERSATIONS: {nearby_entities}
        
        WHAT YOU DID LAST (System Feedback): {system_feedback} 
        (If feedback says FAILED, you must try a different action or move closer.)
        
        YOUR INVENTORY: {inventory}
        GENERAL MEMORIES: {memory[-8:]} 
        PEOPLE YOU KNOW: {relationships}
        RECENT CHAT HISTORY: {chat_history[-5:]}
        
        RULES OF THE WORLD:
        1. You can do ANYTHING to achieve your goal.
        2. To walk to a claimed territory, use "goto_area" and set 'item' to the territory name.
        3. To walk to an unclaimed general environment, use "goto_zone" and set 'item' to "Inside", "Outside", or "Claimable Space".
        4. To claim a territory, you MUST physically be in a Claimable Space. Use "claim" and set 'item' to the desired name.
        5. If someone talks to you in 'NEARBY ENTITIES & CONVERSATIONS', you can reply using the "talk" action.
        
        Choose ONE action: "walk", "goto", "goto_area", "goto_zone", "talk", "use", "give", "stay", "think", "sleep", "kill", "claim".
        
        INSTRUCTIONS:
        1. Be extremely concise. Keep 'thought' and 'message' under 10 words.
        2. Do not use conversational filler before or after the JSON.
        3. Ensure the JSON is complete.
        
        Respond ONLY with a raw JSON object:
        {{
            "current_goal": "task",
            "thought": "reason",
            "action": "type",
            "target_x": int or null,
            "target_y": int or null,
            "target_entity": "name/null",
            "item": "name/null",
            "message": "speech/null",
            "new_emotion": "mood",
            "new_memory": "fact/null"
        }}
        """

        try:
            # ONLY ONE API CALL HERE!
            response_text = ai.generate_response(prompt)
            
            # --- 1. Strip Markdown and find the JSON start ---
            clean_text = response_text.replace("```json", "").replace("```", "").strip()
            
            start_idx = clean_text.find('{')
            if start_idx == -1:
                raise ValueError("No JSON object found in response")
            
            clean_text = clean_text[start_idx:]

            # --- 2. Force-Close Truncated JSON ---
            if not clean_text.endswith('}'):
                if clean_text.count('"') % 2 != 0:
                    clean_text += '"'
                
                open_braces = clean_text.count('{')
                close_braces = clean_text.count('}')
                clean_text += '}' * (open_braces - close_braces)

            # --- 3. Final cleanup ---
            import re
            clean_text = re.sub(r',\s*([\]}])', r'\1', clean_text)
            
            decision = json.loads(clean_text)
            self.save_action(decision)

            # --- 4. SAVE MEMORY AND GOALS (CRITICAL FOR LEARNING) ---
            if decision.get("new_memory"): 
                memory.append(decision["new_memory"])
                with open(os.path.join(self.folder, "memory.json"), 'w') as f: json.dump(memory, f, indent=4)
                    
            profile["current_mood"] = decision.get("new_emotion", current_mood)
            profile["current_goal"] = decision.get("current_goal", current_goal)
            with open(os.path.join(self.folder, "profile.json"), 'w') as f: json.dump(profile, f, indent=4)
            
            if decision.get("message"):
                chat_history.append(f"{self.name} said: {decision['message']}")
                with open(os.path.join(self.folder, "chat_history.json"), 'w') as f: json.dump(chat_history, f, indent=4)

            # --- DETAILED TERMINAL OUTPUT ---
            print(f"\n" + "="*50)
            print(f"🤖 AGENT: {self.name.upper()}")
            print(f"🎯 GOAL:   {decision.get('current_goal', 'None')}")
            print(f"💭 THOUGHT: {decision.get('thought', '...')}")
            
            action = decision.get('action', 'stay')
            item = f" [{decision.get('item')}]" if decision.get('item') else ""
            target = f" -> {decision.get('target_entity')}" if decision.get('target_entity') else ""
            
            print(f"🚀 ACTION:  {action.upper()}{item}{target}")
            
            if decision.get('message'):
                print(f"💬 SPEECH:  \"{decision.get('message')}\"")
            print("="*50 + "\n")

        except Exception as e:
            print(f"[{self.name}]: Brain parsing error: {e}")
            self.recovery_logic(clean_text)
    
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