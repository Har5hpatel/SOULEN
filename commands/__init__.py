"""Command dispatcher: runs offline rules in order."""
from commands.pc_commands import RULES


def dispatch(text: str):
    """Return a reply if an offline rule matches, otherwise None."""
    cleaned = text.lower().strip()
    for rule in RULES:
        reply = rule(cleaned)
        if reply is not None:
            return reply
    return None