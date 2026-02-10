# agents/validator_agent.py
from autogen import AssistantAgent
import os

def create_validator_agent():
    return AssistantAgent(
        name="validator",
        system_message="Fix and validate the code. Do not ask questions.",
        llm_config={
            "api_key": os.getenv("GROQ_API_KEY"),
            "model": "llama-3.3-70b-versatile",   # VALID MODEL
        },
        human_input_mode="NEVER",
    )
