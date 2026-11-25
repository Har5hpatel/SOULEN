"""Prints the model names your Groq and Gemini keys can actually use."""
import json
import os
import urllib.request

import brain.router  # loads your .env keys


def get(url, headers):
    req = urllib.request.Request(url, headers={"User-Agent": "SOULEN/0.1", **headers})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


groq_key = os.environ.get("GROQ_API_KEY")
if groq_key:
    print("--- GROQ ---")
    try:
        data = get("https://api.groq.com/openai/v1/models",
                   {"Authorization": f"Bearer {groq_key}"})
        for m in sorted(x["id"] for x in data["data"]):
            print(m)
    except Exception as e:
        print("failed:", e)

gemini_key = os.environ.get("GEMINI_API_KEY")
if gemini_key:
    print("--- GEMINI ---")
    try:
        data = get("https://generativelanguage.googleapis.com/v1beta/models",
                   {"x-goog-api-key": gemini_key})
        for m in data["models"]:
            if "generateContent" in m.get("supportedGenerationMethods", []):
                print(m["name"].replace("models/", ""))
    except Exception as e:
        print("failed:", e)