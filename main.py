import subprocess
import sys
import threading
import os
import json

# --- 1. The God Mode Listener ---
def terminal_god_mode():
    print("\n" + "="*50)
    print("👑 GOD MODE CONSOLE ACTIVE 👑")
    print("Type a command anywhere in this terminal and press Enter.")
    print("Example 1: 'Bob go to the Kitchen'")
    print("Example 2: 'It is raining outside'")
    print("="*50 + "\n")

    while True:
        try:
            # This waits invisibly for you to type something and hit Enter
            command = input() 
            if not command.strip(): 
                continue

            # Find all valid character folders dynamically
            valid_chars = []
            if os.path.exists("characters"):
                valid_chars = [d for d in os.listdir("characters") if os.path.isdir(os.path.join("characters", d))]

            target_char = None
            command_lower = command.lower()

            # Find who is mentioned FIRST in the sentence
            # (e.g., "bob wants to kill pete" -> Bob gets the command)
            best_index = 9999
            for char in valid_chars:
                idx = command_lower.find(char.lower())
                if idx != -1 and idx < best_index:
                    best_index = idx
                    target_char = char

            # Route the command
            if target_char:
                path = os.path.join("characters", target_char, "commands.json")
                with open(path, 'w') as f: 
                    json.dump({"goal": command}, f, indent=4)
                print(f"⚡ [GOD MODE] Injected Command into {target_char.upper()}: '{command}'")
            else:
                with open("global_context.txt", "a") as f: 
                    f.write(f"\n[God Event]: {command}")
                print(f"🌍 [GOD MODE] World Context Updated: '{command}'")

        except EOFError:
            break  # Gracefully handles the terminal closing
        except Exception as e:
            print(f"Console Error: {e}")

# --- 2. Boot Sequence ---
print("🌍 Starting World Simulation...")

# Start the God Mode listener in a background thread so it doesn't freeze the boot sequence
god_thread = threading.Thread(target=terminal_god_mode, daemon=True)
god_thread.start()

# Start the AI Brains in the background
# This runs brain.py, which loops through the character folders and updates their JSONs
brain_process = subprocess.Popen([sys.executable, "brain.py"])
print("🧠 AI Brain process connected.")

# Start the Pygame Engine
# This runs engine.py, which reads the JSONs, draws the screen, and handles physics
print("🎮 Booting Game Engine...")
engine_process = subprocess.Popen([sys.executable, "engine.py"])

# Keep running until you close the Pygame window
engine_process.wait()

# Clean shutdown: Kill the AI brain when you close the game
print("🛑 Shutting down AI Brains...")
brain_process.terminate()
print("Simulation complete.")