"""SOULEN brain router (Step 3): internet check, then Groq -> Gemini -> OpenAI -> local."""
import json
import os
import socket
import urllib.error
import urllib.request
from pathlib import Path

from brain.local_llm import local_brain

ROOT = Path(__file__).resolve().parent.parent

SYSTEM_PROMPT = (
    "You are SOULEN, a concise personal assistant on the user's PC. "
    "Answer in 1-3 short sentences unless asked for more. "
    "If you are not sure about a fact, say so instead of guessing."
)


def _load_env() -> None:
    """Read keys from D:\\SOULEN\\.env into environment variables."""
    env_file = ROOT / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_env()


def is_online() -> bool:
    """Quick internet check (about 2 seconds max)."""
    try:
        socket.create_connection(("1.1.1.1", 53), timeout=2).close()
        return True
    except OSError:
        return False


def _post(url: str, payload: dict, headers: dict) -> dict:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "User-Agent": "SOULEN/0.1",  # some APIs block the default Python agent
            **headers,
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def _chat_messages(messages: list[dict]) -> list[dict]:
    chat = []
    for m in messages:
        if m["role"] in ("user", "assistant"):
            chat.append({"role": m["role"], "content": m["content"]})
        elif m["role"] == "tool":
            chat.append({"role": "user", "content": f"Tool result: {m['content']}"})
    while chat and chat[0]["role"] != "user":
        chat.pop(0)
    return chat


def _openai_style(url: str, key: str, model: str, messages: list[dict]) -> str:
    """Works for both Groq and OpenAI (same request format)."""
    payload = {
        "model": model,
        "messages": [{"role": "system", "content": SYSTEM_PROMPT}] + _chat_messages(messages),
        "max_tokens": 300,
        "temperature": 0.5,
    }
    data = _post(url, payload, {"Authorization": f"Bearer {key}"})
    return data["choices"][0]["message"]["content"].strip()


def _gemini(key: str, model: str, messages: list[dict]) -> str:
    contents = [
        {
            "role": "model" if m["role"] == "assistant" else "user",
            "parts": [{"text": m["content"]}],
        }
        for m in _chat_messages(messages)
    ]
    payload = {
        "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": contents,
        "generationConfig": {"maxOutputTokens": 800, "temperature": 0.5},
    }
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    data = _post(url, payload, {"x-goog-api-key": key})
    return data["candidates"][0]["content"]["parts"][0]["text"].strip()


def _providers() -> list:
    """Cloud brains in priority order. A provider is skipped if it has no key."""
    providers = []
    groq_key = os.environ.get("GROQ_API_KEY")
    if groq_key:
        model = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
        providers.append((
            "groq",
            lambda m: _openai_style(
                "https://api.groq.com/openai/v1/chat/completions", groq_key, model, m
            ),
        ))
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if gemini_key:
        model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
        providers.append(("gemini", lambda m: _gemini(gemini_key, model, m)))
    openai_key = os.environ.get("OPENAI_API_KEY")
    if openai_key:
        model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
        providers.append((
            "openai",
            lambda m: _openai_style(
                "https://api.openai.com/v1/chat/completions", openai_key, model, m
            ),
        ))
    return providers


def route(messages: list[dict]) -> dict:
    """Try each cloud brain in order, then fall back to the local model."""
    if not is_online():
        print("  [brain] offline, using local model")
        return local_brain(messages)

    for name, ask in _providers():
        try:
            text = ask(messages)
            if text:
                print(f"  [brain] {name}")
                return {"text": text}
        except urllib.error.HTTPError as e:
            if e.code == 429:
                print(f"  [brain] {name} rate limited, trying next...")
            else:
                detail = e.read().decode("utf-8", errors="ignore")[:150]
                print(f"  [brain] {name} failed (HTTP {e.code}): {detail}")
        except Exception as e:
            print(f"  [brain] {name} failed: {e}")

    print("  [brain] cloud unavailable, using local model")
    return local_brain(messages)