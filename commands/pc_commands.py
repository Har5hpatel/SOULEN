"""SOULEN offline PC commands (Step 2). No internet, no tokens."""
import re
import subprocess
import threading
from datetime import datetime, timedelta

import psutil

try:
    import winsound
except ImportError:  # not on Windows
    winsound = None

# Only apps in this list can be opened. Add your own here.
APPS = {
    "notepad": "notepad",
    "calculator": "calc",
    "paint": "mspaint",
    "file explorer": "explorer",
    "explorer": "explorer",
    "chrome": "chrome",
    "browser": "chrome",
    "vs code": "code",
    "spotify": "spotify:",
    "task manager": "taskmgr",
    "settings": "ms-settings:",
}

UNIT_SECONDS = {"second": 1, "sec": 1, "minute": 60, "min": 60, "hour": 3600, "hr": 3600}


def _ring(message: str) -> None:
    """Called when a timer or alarm fires."""
    print(f"\n  *** {message} ***")
    if winsound:
        for _ in range(3):
            winsound.Beep(1000, 300)
    print("You > ", end="", flush=True)


def _schedule(seconds: float, message: str) -> None:
    t = threading.Timer(seconds, _ring, args=(message,))
    t.daemon = True  # won't block SOULEN from exiting
    t.start()


def current_time(text: str):
    if re.search(r"\btime\b", text):
        return datetime.now().strftime("It's %I:%M %p.")
    return None


def current_date(text: str):
    if re.search(r"\bdate\b|what day", text):
        return datetime.now().strftime("Today is %A, %d %B %Y.")
    return None


def system_stats(text: str):
    if not re.search(r"\b(cpu|ram|memory|battery|disk|stats|system)\b", text):
        return None
    cpu = psutil.cpu_percent(interval=0.5)
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage("C:\\")
    lines = [
        f"CPU: {cpu}%",
        f"RAM: {ram.percent}% used ({ram.used / 1e9:.1f} of {ram.total / 1e9:.1f} GB)",
        f"Disk C: {disk.percent}% used",
    ]
    battery = psutil.sensors_battery()
    if battery:
        lines.append(f"Battery: {battery.percent:.0f}%")
    return "\n".join(lines)


def set_timer(text: str):
    if "timer" not in text:
        return None
    m = re.search(r"(\d+)\s*(second|sec|minute|min|hour|hr)s?", text)
    if not m:
        return "How long? Try: set a timer for 5 minutes."
    amount, unit = int(m.group(1)), m.group(2)
    _schedule(amount * UNIT_SECONDS[unit], f"Timer done ({amount} {unit})")
    return f"Timer set for {amount} {unit}."


def set_alarm(text: str):
    if "alarm" not in text:
        return None
    m = re.search(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)?", text)
    if not m:
        return "What time? Try: set an alarm for 7:30 am."
    hour, minute, meridian = int(m.group(1)), int(m.group(2) or 0), m.group(3)
    if meridian == "pm" and hour < 12:
        hour += 12
    elif meridian == "am" and hour == 12:
        hour = 0
    if hour > 23 or minute > 59:
        return "That doesn't look like a valid time."

    now = datetime.now()
    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if target <= now:
        target += timedelta(days=1)
    _schedule((target - now).total_seconds(), f"ALARM {target.strftime('%I:%M %p')}")
    return f"Alarm set for {target.strftime('%I:%M %p')} ({target.strftime('%A')})."


def open_app(text: str):
    m = re.match(r"\s*(?:open|launch)\s+(.+)", text)
    if not m:
        return None
    name = re.sub(r"^(the|my)\s+", "", m.group(1).strip())
    for key, target in APPS.items():
        if key in name:
            subprocess.Popen(f'start "" "{target}"', shell=True)
            return f"Opening {key}."
    return f"I don't know an app called '{name}'. Add it to APPS in pc_commands.py."


# Order matters: first rule that returns a reply wins.
RULES = [set_timer, set_alarm, open_app, system_stats, current_time, current_date]