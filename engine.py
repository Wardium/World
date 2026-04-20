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
class TimeSystem:
    def __init__(self):
        self.tick_rate = 1.0 # 1 real second = 1 in-game minute (adjust for speed)
        self.last_update = time.time()
        
        self.minute = 0
        self.hour = 8   # Start at 8 AM
        self.day = 1
        self.seasons = ["Spring", "Summer", "Autumn", "Winter"]
        self.current_season_index = 0

    def update(self):
        now = time.time()
        if now - self.last_update >= self.tick_rate:
            self.minute += 1
            self.last_update = now

            if self.minute >= 60:
                self.minute = 0
                self.hour += 1
            
            if self.hour >= 24:
                self.hour = 0
                self.day += 1
                
                # Change season every 30 days
                if self.day > 30:
                    self.day = 1
                    self.current_season_index = (self.current_season_index + 1) % 4

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
        
        # Load the base profile (creates one if it doesn't exist)
        self.profile = self.load_json("profile.json", {"name": folder_name, "color": [150, 150, 150]})
        self.name = self.profile.get("name", folder_name)
        self.color = tuple(self.profile.get("color", [150, 150, 150]))
        
        # Starting position
        self.x, self.y = POIS.get("HOME", (400, 300))
        self.speed = 2
        
        # Target managed by AI
        self.target_poi = None 

    def load_json(self, filename, default_data):
        filepath = os.path.join(self.folder_path, filename)
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                return json.load(f)
        else:
            # Create file if missing to set up the system
            os.makedirs(self.folder_path, exist_ok=True)
            with open(filepath, 'w') as f:
                json.dump(default_data, f, indent=4)
            return default_data

    def write_world_state(self, time_dict):
        # The engine writes this so the external AI knows what's happening
        state = {
            "time": time_dict,
            "current_location": {"x": self.x, "y": self.y},
            "status": "idle"
        }
        filepath = os.path.join(self.folder_path, "world_state.json")
        with open(filepath, 'w') as f:
            json.dump(state, f, indent=4)

    def read_ai_action(self):
        # The engine reads this to see what the AI decided to do
        action_data = self.load_json("action.json", {"target_poi": None, "current_thought": "Waiting for AI..."})
        self.target_poi = action_data.get("target_poi")

    def update_movement(self):
        if self.target_poi and self.target_poi in POIS:
            target_x, target_y = POIS[self.target_poi]
            dx, dy = target_x - self.x, target_y - self.y
            distance = ((dx**2) + (dy**2))**0.5

            if distance > self.speed:
                self.x += (dx / distance) * self.speed
                self.y += (dy / distance) * self.speed
            else:
                self.target_poi = None # Arrived

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), 15)
        # Draw name above character
        font = pygame.font.SysFont(None, 24)
        img = font.render(self.name, True, (255, 255, 255))
        screen.blit(img, (self.x - 15, self.y - 25))


# --- 3. The Main Engine ---
class Engine:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((800, 600))
        pygame.display.set_caption("AI Sandbox")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 36)
        
        self.time_system = TimeSystem()
        self.characters = []
        self.load_characters()

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

    def run(self):
        running = True
        update_timer = time.time()

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            # Update Time
            self.time_system.update()

            # Every 2 seconds, write the world state for the AI, and read the AI's response
            if time.time() - update_timer > 2.0:
                time_state = self.time_system.get_state_dict()
                for char in self.characters:
                    char.write_world_state(time_state)
                    char.read_ai_action()
                update_timer = time.time()

            # Update Physical World
            self.screen.fill((30, 30, 30)) # Dark gray background for now

            for char in self.characters:
                char.update_movement()
                char.draw(self.screen)

            # Draw Time HUD
            time_text = self.font.render(self.time_system.get_time_string(), True, (255, 255, 255))
            self.screen.blit(time_text, (10, 10))

            pygame.display.flip()
            self.clock.tick(60)

if __name__ == "__main__":
    game = Engine()
    game.run()