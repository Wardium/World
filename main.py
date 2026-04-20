import subprocess
import sys

print("🌍 Starting World Simulation...")

# 1. Start the AI Brains in the background
# This runs brain.py, which loops through the character folders and updates their JSONs
brain_process = subprocess.Popen([sys.executable, "brain.py"])
print("🧠 AI Brain process connected.")

# 2. Start the Pygame Engine
# This runs engine.py, which reads the JSONs, draws the screen, and handles physics
print("🎮 Booting Game Engine...")
engine_process = subprocess.Popen([sys.executable, "engine.py"])

# 3. Keep running until you close the Pygame window
engine_process.wait()

# 4. Clean shutdown: Kill the AI brain when you close the game
print("🛑 Shutting down AI Brains...")
brain_process.terminate()
print("Simulation complete.")