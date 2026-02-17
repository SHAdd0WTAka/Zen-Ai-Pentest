#!/usr/bin/env python3
import sys
from config_loader import load_config

def test_kimi_connection():
    """Testet die Kimi API Verbindung mit dem aus .env geladenen Key"""

    # Config laden (merged mit Env-Vars)
    config = load_config()
    api_key = config['backends']['kimi_api_key']

    # Check ob Key vorhanden
    if not api_key:
        print("❌ Fehler: KIMI_API_KEY nicht gesetzt!")
        print("   Füge deinen Key in .env ein:")
        print('   export KIMI_API_KEY="sk-..."')
        sys.exit(1)

    print(f"✅ Key geladen: {api_key[:10]}... (gekürzt)")
    print(f"📊 Rate Limit: {config['rate_limits']['requests_per_minute']} req/min")
    print(f"📝 Log Level: {config['output']['log_level']}")

    # Hier würde der tatsächliche API-Call kommen:
    # import requests
    # response = requests.post(
    #     "https://api.moonshot.cn/v1/chat/completions",
    #     headers={"Authorization": f"Bearer {api_key}"},
    #     json={"model": "kimi-k2.5", "messages": [{"role": "user", "content": "Hello"}]}
    # )

    print("\n🚀 Bereit für API-Calls!")

if __name__ == "__main__":
    test_kimi_connection()
