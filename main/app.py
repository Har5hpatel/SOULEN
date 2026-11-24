"""SOULEN main loop (Step 1B): tool registry + tool-calling loop."""
from main.tools import TOOLS, run_tool
from commands import dispatch

EXIT_COMMANDS = {"exit", "quit", "bye"}
MAX_STEPS = 5  # safety limit so the loop can never run forever


def fake_brain(messages: list[dict]) -> dict:
    """Stand-in for the LLM. Returns either a tool call or a final reply.

    Later this gets replaced by Groq/Gemini, but returns the same shape:
      {"tool_call": {"name": "...", "args": {...}}}  or  {"text": "..."}
    """
    last = messages[-1]

    # A tool just ran, so turn its result into the final answer.
    if last["role"] == "tool":
        return {"text": last["content"]}

    # Otherwise look at what the user said and decide on a tool.
    words = last["content"].lower().split()
    if "time" in words:
        return {"tool_call": {"name": "get_current_time", "args": {}}}
    if "date" in words or "day" in words:
        return {"tool_call": {"name": "get_current_date", "args": {}}}

    return {"text": f"[placeholder] You said: {last['content']}"}


def handle_input(text: str) -> str:
    """Take the user's text and return SOULEN's reply, using tools if needed."""
    text = text.strip()
    if not text:
        return ""
        # Offline rules first: instant, free, no internet.
    offline_reply = dispatch(text)
    if offline_reply is not None:
        return offline_reply

    messages = [{"role": "user", "content": text}]

    for _ in range(MAX_STEPS):
        response = fake_brain(messages)

        if "text" in response:
            return response["text"]

        call = response["tool_call"]
        print(f"  [tool] calling {call['name']}")
        result = run_tool(call["name"], call.get("args"))
        messages.append({"role": "assistant", "content": f"called {call['name']}"})
        messages.append({"role": "tool", "content": result})

    return "Sorry, I got stuck in a loop."


def main() -> None:
    print(f"SOULEN online. {len(TOOLS)} tools loaded. Type 'exit' to quit.")
    while True:
        try:
            user_text = input("You > ")
        except (EOFError, KeyboardInterrupt):
            print("\nSOULEN offline. Goodbye.")
            break

        if user_text.strip().lower() in EXIT_COMMANDS:
            print("SOULEN offline. Goodbye.")
            break

        reply = handle_input(user_text)
        if reply:
            print(f"SOULEN > {reply}")


if __name__ == "__main__":
    main()