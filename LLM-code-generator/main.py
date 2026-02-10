import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

print("API KEY LOADED:", api_key is not None)

# Import AFTER env is loaded
from workflows.interaction import run_interaction

# Take user input in real time
if __name__ == "__main__":
    import sys
    prompt = sys.argv[1] if len(sys.argv) > 1 else "Generate a Python function"
    response = run_interaction(prompt)
    print(response)
