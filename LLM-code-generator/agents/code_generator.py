import os
import requests

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
url = "https://api.groq.com/openai/v1/chat/completions"

def run_code_generation(prompt: str):
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "llama-3.3-70b-versatile",  # NEW & SUPPORTED MODEL 
        "messages": [
            {"role": "system", "content": "You generate valid, clean Python code only."},
            {"role": "user", "content": prompt}
        ]
    }

    response = requests.post(url, headers=headers, json=data)
    res = response.json()
    print("🟢 API RAW RESPONSE:", res)

    # Error handling
    if "error" in res:
        return f"❌ API ERROR: {res['error']['message']}"
    if "choices" not in res:
        return f"⚠ No 'choices' key in response. Full response: {res}"

    return res["choices"][0]["message"]["content"]
