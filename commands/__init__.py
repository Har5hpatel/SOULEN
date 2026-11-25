"""Command dispatcher: fixes small typos, then runs offline rules in order."""
import re

from commands.pc_commands import APPS, RULES

# Words the rules understand. Typos of these get corrected.
VOCAB = sorted(
    {
        "time", "date", "what", "cpu", "ram", "memory", "battery", "disk",
        "stats", "system", "timer", "alarm", "open", "launch",
        "second", "seconds", "minute", "minutes", "hour", "hours",
    }
    | {word for app in APPS for word in app.split()}
)

# Very short words are too risky to guess, so list common typos by hand.
MANUAL = {
    "tme": "time", "opn": "open", "rma": "ram",
    "pcu": "cpu", "wat": "what", "wht": "what",
}

# Real words that look like command words. Never "fix" these.
PROTECTED = {"lunch", "state", "states", "status", "tamer", "stars", "data"}


def _distance(a: str, b: str) -> int:
    """Edit distance where swapping two neighbouring letters counts as 1."""
    d = [[0] * (len(b) + 1) for _ in range(len(a) + 1)]
    for i in range(len(a) + 1):
        d[i][0] = i
    for j in range(len(b) + 1):
        d[0][j] = j
    for i in range(1, len(a) + 1):
        for j in range(1, len(b) + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            d[i][j] = min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + cost)
            if i > 1 and j > 1 and a[i - 1] == b[j - 2] and a[i - 2] == b[j - 1]:
                d[i][j] = min(d[i][j], d[i - 2][j - 2] + 1)
    return d[len(a)][len(b)]


def _is_typo_of(word: str, target: str) -> bool:
    d = _distance(word, target)
    if len(target) <= 4:
        # Short targets: only swapped letters (tiem -> time), nothing looser.
        return d == 1 and sorted(word) == sorted(target)
    if len(target) >= 9:
        return d <= 2
    return d <= 1


def fix_typos(text: str) -> str:
    """Correct near-miss words, e.g. 'tiem' -> 'time', 'notepaad' -> 'notepad'."""
    def fix(match: re.Match) -> str:
        word = match.group(0)
        if word in VOCAB or word in PROTECTED:
            return word
        if word in MANUAL:
            return MANUAL[word]
        if len(word) < 4:
            return word
        for target in VOCAB:
            if abs(len(word) - len(target)) <= 2 and _is_typo_of(word, target):
                return target
        return word

    return re.sub(r"[a-z]+", fix, text)


def dispatch(text: str):
    """Return a reply if an offline rule matches, otherwise None."""
    cleaned = fix_typos(text.lower().strip())
    for rule in RULES:
        reply = rule(cleaned)
        if reply is not None:
            return reply
    return None