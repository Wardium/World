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
# --- 2. Character Logic ---
class Character:
    def __init__(self, folder_name):
        import random
        self.folder_path = os.path.join(BASE_CHAR_PATH, folder_name)
        
        if not os.path.exists(self.folder_path):
            os.makedirs(self.folder_path)

        self.ensure_file("profile.json", {
            "name": folder_name, 
            "color": [random.randint(50, 255), random.randint(50, 255), random.randint(50, 255)], 
            "current_mood": "Neutral"
        })
        self.ensure_file("inventory.json", ["Apple", "Keys"])
        self.ensure_file("memory.json", ["I just arrived in this world."])
        self.ensure_file("action.json", {
            "action": "idle",
            "thought": "Just spawned in.",
            "message": ""
        })
        self.ensure_file("world_state.json", {
            "time": "Unknown",
            "current_location": {"x": 0, "y": 0},
            "nearby_entities": [],
            "status": "idle"
        })

        self.profile = self.load_json("profile.json", {})
        self.name = self.profile.get("name", folder_name)
        self.color = tuple(self.profile.get("color", [150, 150, 150]))
        
        self.x, self.y = random.randint(100, 700), random.randint(100, 500)
        self.speed = 1.5
        
        # AI Tracking Variables
        self.action_data = {}
        self.dialogue = ""
        self.dialogue_timer = 0
        self.target_x = None
        self.target_y = None
        self.follow_target = None # New variable for "goto"
        
        self.status = "active"
        self.death_time = None
        self.system_feedback = "None"

    def ensure_file(self, filename, default_content):
        filepath = os.path.join(self.folder_path, filename)
        if not os.path.exists(filepath):
            try:
                with open(filepath, 'w') as f:
                    json.dump(default_content, f, indent=4)
            except Exception as e:
                print(f"❌ Failed to create {filename} for {self.name}: {e}")

    def load_json(self, filename, default_data):
        filepath = os.path.join(self.folder_path, filename)
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return default_data
        return default_data

    # FIXED: Now takes 4 arguments (self, time, characters, map)
    def write_world_state(self, time_dict, all_characters, collision_map):
        nearby = []
        for other in all_characters:
            if other.name != self.name and getattr(other, "status", "active") != "dead":
                dist = ((other.x - self.x)**2 + (other.y - self.y)**2)**0.5
                if dist < 150:
                    # NEW: Include what they are currently saying!
                    if other.dialogue:
                        nearby.append(f"{other.name} (Saying: '{other.dialogue}')")
                    else:
                        nearby.append(other.name)

        zone = "Unknown"
        try:
            if 0 <= int(self.x) < 1080 and 0 <= int(self.y) < 1080:
                color = collision_map.get_at((int(self.x), int(self.y)))
                r, g, b = int(color.r), int(color.g), int(color.b)
                if g > r + 40 and g > b + 40: zone = "Inside"
                elif r > 100 and g > 100 and b < 80 and abs(r - g) < 50: zone = "Outside"
                elif r > g + 40 and r > b + 40: zone = "Claimable Space"
        except Exception:
            pass

        # --- NEW: Check if currently traveling ---
        is_busy = False
        if self.target_x is not None or self.follow_target is not None:
            is_busy = True

        state = {
            "time": time_dict,
            "current_location": {"x": int(self.x), "y": int(self.y)},
            "current_zone": zone,
            "nearby_entities": nearby,
            "status": getattr(self, "status", "active"),
            "last_action_feedback": getattr(self, "system_feedback", "None"),
            "is_busy": is_busy # Pass the flag to the Brain!
        }
        import os, json
        with open(os.path.join(self.folder_path, "world_state.json"), 'w') as f:
            json.dump(state, f, indent=4)
            
        if self.system_feedback != "None":
            self.system_feedback = "None"

    def read_ai_action(self):
        if getattr(self, "status", "active") == "dead": return 

        self.action_data = self.load_json("action.json", {})
        action_type = self.action_data.get("action")
        
        if action_type == "sleep":
            self.status = "sleeping"
            self.dialogue = "Zzz..."
            import time
            self.dialogue_timer = time.time()
            self.target_x, self.target_y, self.follow_target = None, None, None
        else:
            self.status = "active" 
            
            if action_type == "walk":
                self.target_x = self.action_data.get("target_x")
                self.target_y = self.action_data.get("target_y")
                self.follow_target = None
            elif action_type == "goto":
                self.follow_target = self.action_data.get("target_entity")
                self.target_x, self.target_y = None, None
            elif action_type in ["talk", "use", "give", "kill", "talk_viewer", "claim"]:
                self.dialogue = self.action_data.get("message", "")
                if self.dialogue:
                    import time
                    self.dialogue_timer = time.time()
                self.target_x, self.target_y, self.follow_target = None, None, None

    def clear_action(self):
        idle_state = {"action": "idle", "thought": "Waiting for next thought...", "message": ""}
        filepath = os.path.join(self.folder_path, "action.json")
        try:
            with open(filepath, 'w') as f:
                json.dump(idle_state, f, indent=4)
        except Exception:
            pass
        self.action_data = idle_state
        self.dialogue = ""

    # FIXED: Now takes collision_map AND all_characters to process "goto" follows
    def update_movement(self, collision_map, all_characters):
        if getattr(self, "status", "active") == "dead": return 
            
        if self.follow_target:
            target_char = next((c for c in all_characters if c.name == self.follow_target), None)
            if target_char and getattr(target_char, "status", "active") != "dead":
                self.target_x, self.target_y = target_char.x, target_char.y
            else:
                self.follow_target = None 
                self.system_feedback = "FAILED: Target disappeared or died."

        if self.target_x is not None and self.target_y is not None:
            dx, dy = self.target_x - self.x, self.target_y - self.y
            distance = ((dx**2) + (dy**2))**0.5

            if self.follow_target and distance < 40:
                self.target_x, self.target_y = None, None
                self.system_feedback = f"SUCCESS: Approached {self.follow_target}."
                return

            if distance > 0:
                move_x = (dx / distance) * self.speed
                move_y = (dy / distance) * self.speed
                next_x = self.x + move_x
                next_y = self.y + move_y
                
                if 0 <= int(next_x) < 1080 and 0 <= int(next_y) < 1080:
                    color = collision_map.get_at((int(next_x), int(next_y)))
                    if color.r > 200 and color.g > 200 and color.b > 200:
                        self.target_x, self.target_y, self.follow_target = None, None, None
                        self.system_feedback = "FAILED: Path blocked by an obstacle."
                        return
                    else:
                        self.x, self.y = next_x, next_y
                else:
                    self.target_x, self.target_y, self.follow_target = None, None, None
                    self.system_feedback = "FAILED: Path out of bounds."

            if not self.follow_target and distance <= self.speed:
                self.x, self.y = self.target_x, self.target_y
                self.target_x, self.target_y = None, None
                self.system_feedback = "SUCCESS: Arrived at destination."

    def draw(self, surface, font):
        import pygame
        import time
        
        status = getattr(self, "status", "active")
        
        if status == "dead":
            if self.death_time and time.time() - self.death_time > 1.5:
                return 

            pygame.draw.circle(surface, (50, 50, 50), (int(self.x), int(self.y)), 15)
            pygame.draw.line(surface, (255, 0, 0), (self.x - 10, self.y - 10), (self.x + 10, self.y + 10), 3)
            pygame.draw.line(surface, (255, 0, 0), (self.x - 10, self.y + 10), (self.x + 10, self.y - 10), 3)
            name_img = font.render(f"{self.name} (DEAD)", True, (100, 100, 100))
            surface.blit(name_img, (self.x - 20, self.y - 35))
            return 
            
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), 15)
        
        mood = self.load_json("profile.json", {}).get("current_mood", "Neutral")
        display_text = f"{self.name} (Sleeping)" if status == "sleeping" else f"{self.name} ({mood})"
        name_img = font.render(display_text, True, (255, 255, 255))
        surface.blit(name_img, (self.x - 20, self.y - 35))
        
        if self.dialogue and (status == "sleeping" or time.time() - self.dialogue_timer < 5):
            chat_img = font.render(self.dialogue, True, (0, 0, 0))
            text_rect = chat_img.get_rect()
            bubble_x, bubble_y = self.x + 15, self.y - 45
            bubble_rect = pygame.Rect(bubble_x, bubble_y, text_rect.width + 16, text_rect.height + 10)
            pygame.draw.rect(surface, (255, 255, 255), bubble_rect, border_radius=8)
            pygame.draw.rect(surface, (0, 0, 0), bubble_rect, width=2, border_radius=8)
            surface.blit(chat_img, (bubble_x + 8, bubble_y + 5))


# --- 3. The Main Engine ---
class Engine:
    def __init__(self):
        pygame.init()
        # The window you actually see (starts at 800x800 but can be resized)
        self.screen = pygame.display.set_mode((800, 800), pygame.RESIZABLE) 
        pygame.display.set_caption("World")
        
        # The internal world that is permanently 1080x1080
        self.canvas = pygame.Surface((1080, 1080)) 
        
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 24) # Slightly smaller font fits bubbles better
        
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
            self.collision_map.fill((0, 0, 0))
        
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
            
            
    def process_kill_action(self, killer, target_name):
        target_char = next((c for c in self.characters if c.name == target_name), None)
        
        if target_char and target_char.status != "dead":
            target_char.status = "dead"
            target_char.death_time = time.time() # <--- START THE TIMER
            target_char.dialogue = "" 
            target_char.target_x, target_char.target_y = None, None # <--- HALT MOVEMENT
            print(f"☠️ SYSTEM: {killer.name} killed {target_char.name}!")
            
            target_char.profile["current_mood"] = "Dead"
            with open(os.path.join(target_char.folder_path, "profile.json"), 'w') as f:
                json.dump(target_char.profile, f, indent=4)      

    def run(self):
        running = True
        import time
        update_timer = time.time()

        while running:
            # --- Event Loop (Now handles Resizing) ---
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.VIDEORESIZE:
                    # Update the window size, but keep the canvas logic identical
                    self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)

            # --- 1. Update Time ---
            self.time_system.update()

            # --- 2. AI & Data Radar ---
            if time.time() - update_timer > 2.0:
                self.check_for_new_characters()
                
                time_state = self.time_system.get_state_dict()
                
                for char in self.characters:
                    char.profile = char.load_json("profile.json", char.profile)
                    char.name = char.profile.get("name", char.name)
                    char.color = tuple(char.profile.get("color", char.color))

                    # PASS COLLISION MAP HERE for Semantic Radar
                    char.write_world_state(time_state, self.characters, self.collision_map)
                    char.read_ai_action()
                    
                    # --- NEW LOGIC HOOKED UP HERE ---
                    
                    # 1. If they are dead, skip to the next character. No zombies allowed.
                    if getattr(char, "status", "active") == "dead":
                        continue 

                    # 2. Process Claim, Give, Kill, Use, Goto Zone, and Goto Area actions
                    action_type = char.action_data.get("action")
                    
                    if action_type == "claim":
                        # 1. Verify physical location using the map
                        try:
                            color = self.collision_map.get_at((int(char.x), int(char.y)))
                            is_red = int(color.r) > int(color.g) + 40 and int(color.r) > int(color.b) + 40
                        except:
                            is_red = False
                            
                        if not is_red:
                            char.system_feedback = "FAILED: You must physically stand inside a Red area to claim it."
                        else:
                            # 2. Verify it hasn't been claimed yet
                            already_claimed = False
                            zone_name = char.action_data.get("item", "My Room")
                            
                            import os, re
                            if os.path.exists("global_context.txt"):
                                with open("global_context.txt", "r") as f:
                                    for line in f:
                                        if "[Territory]" in line:
                                            match = re.search(r"X:(\d+), Y:(\d+)", line)
                                            if match:
                                                cx, cy = int(match.group(1)), int(match.group(2))
                                                dist = ((char.x - cx)**2 + (char.y - cy)**2)**0.5
                                                if dist < 80: 
                                                    already_claimed = True
                                                    break
                            
                            if already_claimed:
                                char.system_feedback = "FAILED: This red area has already been claimed by someone."
                            else:
                                claim_msg = f"\n[Territory] The red zone near X:{int(char.x)}, Y:{int(char.y)} is claimed by {char.name} as: {zone_name}"
                                with open("global_context.txt", "a") as f: f.write(claim_msg)
                                char.system_feedback = f"SUCCESS: Claimed territory as {zone_name}."
                                print(f"🚩 SYSTEM: {char.name} successfully claimed {zone_name}!")
                        
                        char.clear_action()

                    elif action_type == "goto_area":
                        import os, re, random
                        area_name = char.action_data.get("item")
                        found = False
                        if os.path.exists("global_context.txt"):
                            with open("global_context.txt", "r") as f:
                                for line in f:
                                    if f"as: {area_name}" in line:
                                        match = re.search(r"X:(\d+), Y:(\d+)", line)
                                        if match:
                                            # Pick a random point within 60 pixels of the claimed center
                                            char.target_x = int(match.group(1)) + random.randint(-60, 60)
                                            char.target_y = int(match.group(2)) + random.randint(-60, 60)
                                            char.system_feedback = f"SUCCESS: Found {area_name}. Navigating there now."
                                            found = True
                                            break
                        if not found:
                            char.system_feedback = f"FAILED: Could not find territory '{area_name}' in the world."
                        char.clear_action()

                    elif action_type == "goto_zone":
                        import random
                        target_zone = char.action_data.get("item")
                        found = False
                        
                        # 1. Local Area Scan (Simulating a 300-pixel "Vision Radius")
                        for _ in range(500): 
                            rx = int(char.x) + random.randint(-300, 300)
                            ry = int(char.y) + random.randint(-300, 300)
                            
                            # Make sure we don't look outside the map boundaries
                            if 0 <= rx < 1080 and 0 <= ry < 1080:
                                try:
                                    color = self.collision_map.get_at((rx, ry))
                                    r, g, b = int(color.r), int(color.g), int(color.b)
                                    
                                    match = False
                                    if target_zone == "Inside" and g > r + 40 and g > b + 40: match = True
                                    elif target_zone == "Outside" and r > 100 and g > 100 and b < 80 and abs(r - g) < 50: match = True
                                    elif target_zone == "Claimable Space" and r > g + 40 and r > b + 40: match = True
                                    
                                    if match:
                                        char.target_x, char.target_y = rx, ry
                                        char.system_feedback = f"SUCCESS: Spotted {target_zone} nearby. Walking there."
                                        found = True
                                        break
                                except:
                                    pass
                                    
                        # 2. Search Mode (If they didn't see it, they wander to look for it)
                        if not found:
                            char.target_x = max(50, min(1030, int(char.x) + random.randint(-400, 400)))
                            char.target_y = max(50, min(1030, int(char.y) + random.randint(-400, 400)))
                            char.system_feedback = f"FAILED: Could not see {target_zone} nearby. Wandering to search for it."
                        
                        char.clear_action()
                        
                    elif action_type in ["give", "use", "kill"]:
                        target = char.action_data.get("target_entity")
                        item = char.action_data.get("item")
                        action_allowed = True
                        
                        if target == char.name:
                            print(f"🛑 SYSTEM: {char.name} tried to {action_type} themselves, but that is not allowed!")
                            action_allowed = False
                        elif target:
                            target_char = next((c for c in self.characters if c.name == target), None)
                            if target_char:
                                dist = ((char.x - target_char.x)**2 + (char.y - target_char.y)**2)**0.5
                                if dist > 50:
                                    print(f"🛑 {char.name} is too far away to {action_type} {target}!")
                                    char.system_feedback = f"FAILED: {target} is too far away."
                                    action_allowed = False
                            else:
                                char.system_feedback = f"FAILED: {target} does not exist in this world."
                                action_allowed = False
                                
                        if action_allowed:
                            if action_type == "give" and target and item:
                                self.process_give_action(char, target, item)
                                char.system_feedback = f"SUCCESS: Gave {item} to {target}."
                            elif action_type == "kill" and target:
                                self.process_kill_action(char, target)
                                char.system_feedback = f"SUCCESS: Killed {target}."
                            elif action_type == "use":
                                print(f"🛠️ SYSTEM: {char.name} used {item} on {target}")
                                char.system_feedback = f"SUCCESS: Used {item} on {target}."
                                
                        char.clear_action()
                            
                update_timer = time.time()

            # --- 3. Render Graphics ---
            self.canvas.blit(self.world_map, (0, 0)) 

            for char in self.characters:
                char.update_movement(self.collision_map, self.characters) 
                char.draw(self.canvas, self.font) 

            # Draw Time HUD
            time_text = self.font.render(self.time_system.get_time_string(), True, (255, 255, 255))
            self.canvas.blit(time_text, (10, 10))

            # B. Scale the 1080x1080 canvas to whatever size the window currently is
            window_size = self.screen.get_size()
            scaled_canvas = pygame.transform.smoothscale(self.canvas, window_size)
            
            # C. Blit the final scaled image to the actual monitor
            self.screen.blit(scaled_canvas, (0, 0))

            pygame.display.flip()
            self.clock.tick(60)

if __name__ == "__main__":
    game = Engine()
    game.run()