import pygame
import os
import json
import time

# --- Configuration ---
BASE_CHAR_PATH = "characters"
MAP_IMAGE = "world_map.png"
COLLISION_MAP = "collision_map.png"

# Basic POIs for the AI to target
POIS = {
    "HOME": (200, 200),
    "WORK": (600, 200),
    "STORE": (400, 500)
}

# --- 1. The Time System ---
# --- 1. The Time System ---
class TimeSystem:
    def __init__(self):
        self.tick_rate = 0.5 # 0.5 real seconds = 1 in-game minute (Twice as fast)
        self.last_update = time.time()
        self.save_file = "global_time.json"
        
        # Load saved time if it exists
        saved_data = {}
        if os.path.exists(self.save_file):
            try:
                with open(self.save_file, 'r') as f:
                    saved_data = json.load(f)
            except:
                pass
                
        self.minute = saved_data.get("minute", 0)
        self.hour = saved_data.get("hour", 8)
        self.day = saved_data.get("day", 1)
        self.seasons = ["Spring", "Summer", "Autumn", "Winter"]
        self.current_season_index = saved_data.get("season_index", 0)

    def save_time(self):
        with open(self.save_file, 'w') as f:
            json.dump({
                "minute": self.minute,
                "hour": self.hour,
                "day": self.day,
                "season_index": self.current_season_index
            }, f)

    def update(self):
        now = time.time()
        if now - self.last_update >= self.tick_rate:
            self.minute += 1
            self.last_update = now

            if self.minute >= 60:
                self.minute = 0
                self.hour += 1
                self.save_time() # Save game every hour to avoid spamming the hard drive
            
            if self.hour >= 24:
                self.hour = 0
                self.day += 1
                
                # Repeat to 0 after 11 days
                if self.day >= 11:
                    self.day = 0
                    self.current_season_index = (self.current_season_index + 1) % 4
                
                self.save_time()

    def get_time_string(self):
        season = self.seasons[self.current_season_index]
        return f"Day {self.day} ({season}) - {self.hour:02d}:{self.minute:02d}"
    
    def get_state_dict(self):
        return {
            "day": self.day,
            "season": self.seasons[self.current_season_index],
            "hour": self.hour,
            "minute": self.minute
        }

# --- 2. Character Logic ---
class Character:
    def __init__(self, folder_name):
        self.folder_path = os.path.join(BASE_CHAR_PATH, folder_name)
        os.makedirs(self.folder_path, exist_ok=True) # Ensure folder exists
        
        # 1. Profile (Randomize color so hot-dropped chars look different)
        import random # Make sure 'import random' is at the top of engine.py
        self.profile = self.load_json("profile.json", {
            "name": folder_name, 
            "color": [random.randint(50, 255), random.randint(50, 255), random.randint(50, 255)], 
            "current_mood": "Neutral"
        })
        self.name = self.profile.get("name", folder_name)
        self.color = tuple(self.profile.get("color", [150, 150, 150]))
        
        # Position & Stats
        self.x, self.y = random.randint(100, 700), random.randint(100, 500)
        self.speed = 1.5
        
        # AI Tracking Variables
        self.action_data = {}
        self.dialogue = ""
        self.dialogue_timer = 0
        self.target_x = None
        self.target_y = None

        # --- PRE-MAKE ALL CONTEXT FILES IMMEDIATELY ---
        
        # 2. Inventory & Memory
        self.load_json("inventory.json", ["Apple", "Keys"])
        self.load_json("memory.json", ["I just arrived in this world."])
        
        # 3. Action (Start Idle)
        self.action_data = self.load_json("action.json", {
            "action": "idle",
            "thought": "Just spawned in.",
            "message": ""
        })
        
        # 4. World State (Dummy state until engine updates it)
        self.load_json("world_state.json", {
            "time": "Unknown",
            "current_location": {"x": self.x, "y": self.y},
            "nearby_entities": [],
            "status": "idle"
        })

    # Add this inside your Character class in engine.py
    def clear_action(self):
        """Resets the action file to idle so one-time actions (like 'give') don't loop endlessly."""
        idle_state = {
            "action": "idle", 
            "thought": "Waiting for next thought...",
            "message": ""
        }
        filepath = os.path.join(self.folder_path, "action.json")
        try:
            with open(filepath, 'w') as f:
                json.dump(idle_state, f, indent=4)
        except Exception as e:
            print(f"Could not clear action for {self.name}: {e}")
            
        self.action_data = idle_state
        self.dialogue = "" # Clear speech bubble

    def load_json(self, filename, default_data):
        # ... (keep your existing load_json logic) ...
        filepath = os.path.join(self.folder_path, filename)
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r') as f: return json.load(f)
            except: return default_data
        else:
            os.makedirs(self.folder_path, exist_ok=True)
            with open(filepath, 'w') as f: json.dump(default_data, f, indent=4)
            return default_data

    def write_world_state(self, time_dict, all_characters):
        # Figure out who is nearby (within 150 pixels)
        nearby = []
        for other in all_characters:
            if other.name != self.name:
                dist = ((other.x - self.x)**2 + (other.y - self.y)**2)**0.5
                if dist < 150:
                    nearby.append(other.name)

        state = {
            "time": time_dict,
            "current_location": {"x": int(self.x), "y": int(self.y)},
            "nearby_entities": nearby,
            "status": "active"
        }
        with open(os.path.join(self.folder_path, "world_state.json"), 'w') as f:
            json.dump(state, f, indent=4)

    def read_ai_action(self):
        self.action_data = self.load_json("action.json", {})
        action_type = self.action_data.get("action")
        
        # Parse the new AI commands
        if action_type == "walk":
            self.target_x = self.action_data.get("target_x")
            self.target_y = self.action_data.get("target_y")
        elif action_type in ["talk", "use", "give"]:
            self.dialogue = self.action_data.get("message", "")
            if self.dialogue:
                self.dialogue_timer = time.time()
            self.target_x, self.target_y = None, None # Stop walking to talk/use

    def update_movement(self, collision_map):
        if self.target_x is not None and self.target_y is not None:
            dx, dy = self.target_x - self.x, self.target_y - self.y
            distance = ((dx**2) + (dy**2))**0.5

            if distance > 0: # Prevent dividing by zero
                move_x = (dx / distance) * self.speed
                move_y = (dy / distance) * self.speed
                
                next_x = self.x + move_x
                next_y = self.y + move_y
                
                # Check boundaries of the 1080x1080 map
                if 0 <= int(next_x) < 1080 and 0 <= int(next_y) < 1080:
                    # Check pixel color on the collision map
                    color = collision_map.get_at((int(next_x), int(next_y)))
                    
                    # If RGB values are high (meaning white or near-white)
                    if color.r > 200 and color.g > 200 and color.b > 200:
                        # Wall hit! Clear target and stop.
                        self.target_x, self.target_y = None, None
                        return
                    else:
                        self.x = next_x
                        self.y = next_y
                else:
                    self.target_x, self.target_y = None, None # Arrived or out of bounds

            if distance <= self.speed:
                self.x, self.y = self.target_x, self.target_y
                self.target_x, self.target_y = None, None # Arrived perfectly

    def draw(self, screen, font):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), 15)
        
        # Name and Mood
        mood = self.load_json("profile.json", {}).get("current_mood", "")
        name_img = font.render(f"{self.name} ({mood})", True, (255, 255, 255))
        screen.blit(name_img, (self.x - 20, self.y - 35))
        
        # Dialogue bubble
        if self.dialogue and time.time() - self.dialogue_timer < 5: # Show for 5 secs
            chat_img = font.render(self.dialogue, True, (0, 0, 0), (255, 255, 200))
            screen.blit(chat_img, (self.x + 15, self.y - 15))


# --- 3. The Main Engine ---
class Engine:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((1080, 1080)) # Set map size
        pygame.display.set_caption("AI Sandbox")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 36)
        
        # Load the visual map and collision map
        try:
            self.world_map = pygame.image.load(MAP_IMAGE).convert()
            self.world_map = pygame.transform.scale(self.world_map, (1080, 1080))
            
            self.collision_map = pygame.image.load(COLLISION_MAP).convert()
            self.collision_map = pygame.transform.scale(self.collision_map, (1080, 1080))
        except Exception as e:
            print(f"Error loading maps: {e}. Ensure world_map.png and collision_map.png exist.")
            self.world_map = pygame.Surface((1080, 1080))
            self.world_map.fill((30, 100, 30))
            self.collision_map = pygame.Surface((1080, 1080))
            self.collision_map.fill((0, 0, 0)) # Default to walkable black
        
        self.time_system = TimeSystem()
        self.characters = []
        self.load_characters()

    # Add this inside your Engine class
    def check_for_new_characters(self):
        """Scans the directory while running. If a new folder appears, spawn them."""
        if not os.path.exists(BASE_CHAR_PATH):
            return
            
        current_names = [char.name for char in self.characters]
        
        # Add a blacklist for temporary OS folders and hidden files
        ignored_names = ["new folder", "untitled folder", "untitled"]
        
        for item in os.listdir(BASE_CHAR_PATH):
            folder_path = os.path.join(BASE_CHAR_PATH, item)
            
            if os.path.isdir(folder_path):
                # Skip hidden folders (like .git or .DS_Store) and temporary OS names
                if item.startswith('.') or item.lower() in ignored_names:
                    continue 
                
                # Check for things like "New folder (2)" 
                if item.lower().startswith("new folder"):
                    continue

                if item not in current_names:
                    print(f"✨ NEW ENTITY DETECTED: {item}. Initializing...")
                    new_char = Character(item)
                    self.characters.append(new_char)

    def load_characters(self):
        """Dynamically loads any folder inside the characters directory."""
        if not os.path.exists(BASE_CHAR_PATH):
            os.makedirs(BASE_CHAR_PATH)
            print(f"Created '{BASE_CHAR_PATH}' directory. Add character folders here.")
            return

        for item in os.listdir(BASE_CHAR_PATH):
            if os.path.isdir(os.path.join(BASE_CHAR_PATH, item)):
                self.characters.append(Character(item))
                print(f"Loaded character: {item}")


    # Add this inside your Engine class in engine.py
    def process_give_action(self, giver, target_name, item_name):
        """Handles the physical transfer of items between character JSONs."""
        # Find the target character in the world
        target_char = next((c for c in self.characters if c.name == target_name), None)
        
        if not target_char:
            print(f"[{giver.name}] tried to give {item_name} to {target_name}, but they aren't here!")
            return

        # Safely load both inventories
        giver_inv = giver.load_json("inventory.json", [])
        target_inv = target_char.load_json("inventory.json", [])

        # Verify the giver actually has the item before transferring
        if item_name in giver_inv:
            giver_inv.remove(item_name)
            target_inv.append(item_name)
            
            # Save inventories back to their respective files
            with open(os.path.join(giver.folder_path, "inventory.json"), 'w') as f:
                json.dump(giver_inv, f, indent=4)
            with open(os.path.join(target_char.folder_path, "inventory.json"), 'w') as f:
                json.dump(target_inv, f, indent=4)
                
            print(f"📦 SYSTEM: {giver.name} successfully gave '{item_name}' to {target_char.name}")
        else:
            print(f"[{giver.name}] tried to give '{item_name}', but it is not in their inventory!")
            

    def run(self):
        running = True
        update_timer = time.time()

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            # --- 1. Update Time (Runs every frame) ---
            self.time_system.update()

            # --- 2. AI & Data Radar (Runs every 2 seconds) ---
            if time.time() - update_timer > 2.0:
                self.check_for_new_characters()
                
                time_state = self.time_system.get_state_dict()
                
                for char in self.characters:
                    char.profile = char.load_json("profile.json", char.profile)
                    char.name = char.profile.get("name", char.name)
                    char.color = tuple(char.profile.get("color", char.color))

                    char.write_world_state(time_state, self.characters)
                    char.read_ai_action()
                    
                    action_type = char.action_data.get("action")
                    if action_type == "give":
                        target = char.action_data.get("target_entity")
                        item = char.action_data.get("item")
                        if target and item:
                            self.process_give_action(char, target, item)
                            char.clear_action()
                            
                update_timer = time.time()

            # --- 3. Render Graphics (Runs every frame) ---
            # IMPORTANT: These lines must be aligned with the 'if' statement above, NOT inside it!
            
            self.screen.blit(self.world_map, (0, 0)) 

            for char in self.characters:
                char.update_movement(self.collision_map) 
                char.draw(self.screen, self.font)

            # Draw Time HUD
            time_text = self.font.render(self.time_system.get_time_string(), True, (255, 255, 255))
            self.screen.blit(time_text, (10, 10))

            pygame.display.flip()
            self.clock.tick(60)

if __name__ == "__main__":
    game = Engine()
    game.run()