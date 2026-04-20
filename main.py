import pygame
import random
import time
import json
import threading

# --- 1. THE AI WRAPPER ---
def generate_ai_response(prompt: str) -> dict:
    """
    This is your 'ai.py'. Right now it mocks an AI response.
    Later, you will replace this with a real API call to OpenAI/Local LLM.
    """
    time.sleep(1) # Simulate the time it takes for a real AI to think
    
    # Randomly decide to either walk somewhere or say something
    action_type = random.choice(["move", "talk", "idle"])
    
    if action_type == "move":
        # AI picks random coordinates to wander to
        return {
            "action": "move",
            "x": random.randint(50, 750),
            "y": random.randint(50, 550),
            "thought": "I feel like taking a walk over there.",
            "dialogue": ""
        }
    elif action_type == "talk":
        return {
            "action": "talk",
            "x": None,
            "y": None,
            "thought": "I have something on my mind.",
            "dialogue": "Beautiful day in the sandbox, isn't it?"
        }
    else:
        return {
            "action": "idle",
            "x": None,
            "y": None,
            "thought": "I'm just going to stand here and chill.",
            "dialogue": ""
        }

# --- 2. THE CHARACTER & BRAIN ---
class Character:
    def __init__(self, name, x, y, color):
        self.name = name
        self.x = x
        self.y = y
        self.color = color
        self.speed = 1.5
        
        # AI State
        self.is_thinking = False
        self.current_action = "idle"
        self.target_x = None
        self.target_y = None
        self.current_thought = "Just spawned in."
        self.current_dialogue = ""
        self.dialogue_timer = 0
        
        # Inventory & Memory (to be passed to the AI later)
        self.inventory = []
        self.memory = ["I just woke up in a void."]

    def start_thinking(self, world_state):
        """Runs the AI request in a background thread so the game doesn't freeze."""
        if not self.is_thinking and self.current_action == "idle":
            self.is_thinking = True
            # Pass the character and world state to the thread
            threading.Thread(target=self._brain_process, args=(world_state,), daemon=True).start()

    def _brain_process(self, world_state):
        """The actual 'Brain' logic. Builds the prompt and asks the AI."""
        # 1. Build the prompt (This is where you'd inject memory, inventory, etc.)
        prompt = f"You are {self.name}. World: {world_state}. What do you do?"
        
        # 2. Get AI Response
        decision = generate_ai_response(prompt)
        
        # 3. Apply the decision back to the engine
        self.current_action = decision.get("action", "idle")
        self.current_thought = decision.get("thought", "")
        self.current_dialogue = decision.get("dialogue", "")
        
        if self.current_action == "move":
            self.target_x = decision.get("x")
            self.target_y = decision.get("y")
        elif self.current_action == "talk":
            self.dialogue_timer = time.time() # Show text box for a few seconds
            self.current_action = "idle" # Go back to idle after speaking
            
        print(f"[{self.name}]: {self.current_thought}")
        self.is_thinking = False

    def update(self, world_state):
        # If we have a destination, walk towards it
        if self.current_action == "move" and self.target_x is not None:
            dx = self.target_x - self.x
            dy = self.target_y - self.y
            distance = ((dx**2) + (dy**2))**0.5
            
            if distance > self.speed:
                self.x += (dx / distance) * self.speed
                self.y += (dy / distance) * self.speed
            else:
                # We arrived!
                self.current_action = "idle"
                self.target_x, self.target_y = None, None
        
        # If we are doing nothing, start thinking about what to do next
        if self.current_action == "idle":
            self.start_thinking(world_state)

    def draw(self, screen, font):
        # Draw character
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), 15)
        
        # Draw name
        name_img = font.render(self.name, True, (200, 200, 200))
        screen.blit(name_img, (self.x - 15, self.y - 25))
        
        # Draw dialogue bubble if talking
        if self.current_dialogue and time.time() - self.dialogue_timer < 4:
            dialogue_img = font.render(self.current_dialogue, True, (0, 0, 0), (255, 255, 255))
            screen.blit(dialogue_img, (self.x + 15, self.y - 40))

# --- 3. THE ENGINE ---
class Engine:
    def __init__(self):
        pygame.init()
        self.width, self.height = 800, 600
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Autonomous AI Sandbox")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 24)
        
        # Create starting characters
        self.characters = [
            Character("Alice", 400, 300, (200, 50, 50)),
            Character("Bob", 200, 100, (50, 50, 200))
        ]

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            # Clear screen
            self.screen.fill((30, 40, 30))

            # Build a simple world state string to pass to the AI
            world_state = f"Time: {time.time()} - Characters alive: {len(self.characters)}"

            # Update and Draw characters
            for char in self.characters:
                char.update(world_state)
                char.draw(self.screen, self.font)

            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()

if __name__ == "__main__":
    game = Engine()
    game.run()