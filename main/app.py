"""SOULEN main loop: offline rules first, then the brain."""
from brain.router import route
from commands import dispatch
from main.tools import TOOLS, run_tool

EXIT_COMMANDS = {"exit", "quit", "bye"}
MAX_STEPS = 5       # safety limit so the loop can never run forever
MAX_HISTORY = 6     # remember the last few messages for context
HISTORY: list[dict] = []


def handle_input(text: str) -> str:
    """Offline rules first. If none match, ask the brain."""
    text = text.strip()
    if not text:
        return ""

    offline_reply = dispatch(text)
    if offline_reply is not None:
        return offline_reply

    user_msg = {"role": "user", "content": text}
    messages = HISTORY[-MAX_HISTORY:] + [user_msg]
    print("  [brain] thinking...")

    for _ in range(MAX_STEPS):
        response = route(messages)

        if "text" in response:
            HISTORY.append(user_msg)
            HISTORY.append({"role": "assistant", "content": response["text"]})
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