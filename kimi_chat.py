#!/usr/bin/env python3
import requests
import sys
from config_loader import load_config

def ask_kimi(prompt, model="kimi-k2.5"):
    """Sendet Prompt an Kimi API und gibt Antwort zurück"""
    
    config = load_config()
    api_key = config['backends']['kimi_api_key']
    
    if not api_key:
        print("❌ KIMI_API_KEY fehlt in .env")
        sys.exit(1)
    
    url = "https://api.moonshot.cn/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        return f"❌ API Error: {e}"

if __name__ == "__main__":
    # Test-Prompt
    if len(sys.argv) > 1:
        prompt = " ".join(sys.argv[1:])
    else:
        prompt = "Erkläre mir SQL Injection in 3 Sätzen."
    
    print(f"🧠 Frage: {prompt}\n")
    print(f"🤖 Antwort:\n{ask_kimi(prompt)}")
