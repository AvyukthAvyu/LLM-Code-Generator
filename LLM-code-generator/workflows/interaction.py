# workflows/interaction.py

from agents.code_generator import run_code_generation

def run_interaction(prompt: str):
    try:
        return run_code_generation(prompt)  # OPENAI only now
    except Exception as e:
        return f"ERROR: {e}"
