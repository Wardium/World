# ai.py
import random

def generate_response(prompt: str) -> str:
    """
    Takes a text prompt and returns a text response.
    REPLACE THE CODE BELOW WITH A REAL API CALL LATER (e.g., OpenAI, Ollama)
    """
    
    # --- MOCK AI BEHAVIOR ---
    # In a real scenario, the AI would read the prompt. 
    # For now, we will just randomly pick a valid choice so the engine doesn't break.
    
    choices = ["HOME", "WORK", "STORE"]
    chosen_poi = random.choice(choices)
    
    # We ask the AI to return JSON so our Brain can easily read it
    mock_json_response = f'''
    {{
        "target_poi": "{chosen_poi}",
        "current_thought": "I looked at my goals and decided to go to {chosen_poi}."
    }}
    '''
    
    return mock_json_response