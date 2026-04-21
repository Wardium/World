import json
import re
from ollamafreeapi import OllamaFreeAPI

# Initialize the client
client = OllamaFreeAPI()

def generate_response(prompt: str) -> str:
    """Sends the massive context prompt to the real LLM and fetches the JSON decision."""
    try:
        response = client.chat(
            model="gpt-oss:20b",
            prompt=prompt,
            temperature=0.7,
            # Increasing tokens helps prevent the cutoff you saw in the debug
            max_tokens=300 
        )
        return response
        
    except Exception as e:
        print(f"⚠️ API Connection Error: {e}")
        # Fallback JSON so the engine doesn't crash if the API fails
        fallback = {
            "current_goal": "Wait for my brain to reconnect.",
            "thought": f"I feel disconnected from reality. (Error: {e})",
            "action": "stay",
            "target_x": None, "target_y": None, "target_entity": None,
            "item": None, "message": None,
            "new_emotion": "Confused", 
            "new_memory": None
        }
        return json.dumps(fallback)