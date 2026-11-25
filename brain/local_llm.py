"""Local offline brain via Ollama (Step 2.5). No internet, no API keys."""
import json
import urllib.error
import urllib.request

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen3.5:2b"

SYSTEM_PROMPT = (
    "You are SOULEN, a concise personal assistant running offline on the "
    "user's PC. Answer in 1-3 short sentences. If you are not sure about a "
    "fact, say so instead of guessing. You cannot browse the internet."
)


def local_brain(messages: list[dict]) -> dict:
    """Same shape as the cloud brains will use: returns {"text": "..."}."""
    chat = [{"role": "system", "content": SYSTEM_PROMPT}]
    for m in messages:
        if m["role"] in ("user", "assistant"):
            chat.append({"role": m["role"], "content": m["content"]})
        elif m["role"] == "tool":
            chat.append({"role": "user", "content": f"Tool result: {m['content']}"})

    payload = {
        "model": MODEL,
        "messages": chat,
        "stream": False,
        "think": False,
        "keep_alive": "2m",  # unload from RAM after 2 idle minutes
        "options": {"num_predict": 200, "temperature": 0.4},
    }
    request = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )

    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            data = json.load(response)
        return {"text": data["message"]["content"].strip()}
    except urllib.error.HTTPError:
        return {"text": f"Model not found. Run: ollama pull {MODEL}"}
    except urllib.error.URLError:
        return {"text": "My local brain isn't running. Start Ollama and try again."}
    except Exception as e:
        return {"text": f"Local brain error: {e}"}