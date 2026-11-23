# SOULEN (Hybrid JARVIS) — Project Map & Roadmap

## 1. Core Concept & Hardware Target
- **Goal:** A lightweight, hybrid PC + Android assistant ("SOULEN") with a cyan/blue Iron Man HUD.
- **Target Machine:** Windows PC, 8GB System RAM, NVIDIA RTX 3050.
- **Memory Rule:** Keep active RAM footprint minimal. Prefer deterministic Python rules and lightweight cloud APIs over running heavy local LLMs all the time.

## 2. Hybrid Execution Flow (Order of Operations)
1. **Offline Rule Engine (`commands/`):** Instant keyword/regex matching for local tasks (time, system stats, opening apps, alarms/timers, ADB phone commands). Works 100% offline with zero token cost.
2. **Connectivity Check (`brain/`):** Quick check if internet is available.
3. **Cloud Brain Router (`brain/`):** If online and no offline rule matched, route to free-tier cloud LLMs with automatic fallback on 429/error:
   - Primary: Groq API (fast, free tier)
   - Secondary: Gemini API (free tier)
   - Optional Tertiary: OpenAI / ChatGPT (only if key is configured)
4. **Graceful Offline Fallback:** If offline and no rule matches (or all cloud APIs fail), respond cleanly without crashing.

## 3. Folder Structure (Actual Layout)
```text
D:\SOLEN\
├── .env                 # Secret API keys (IGNORED by git)
├── .env.example         # Dummy key template (committed to git)
├── .gitignore           # Git ignore rules
├── CLAUDE.md            # Rules for AI pair-programming
├── project_map.md       # This file (architecture & progress)
├── README.md            # Public GitHub overview & daily build log
├── main/                # Entry point, main loop, safety checks, & voice bridge
│   ├── app.py           # Main runner loop (connects commands, brain, & UI)
│   ├── safety.py        # Action logger + [y/N] confirmation prompts
│   └── voice.py         # (Slice 4) Push-to-talk / Wake word, Whisper STT, Piper TTS
├── commands/            # Slice 1 & 6: Deterministic offline actions
│   ├── __init__.py      # Command dispatcher
│   ├── pc_commands.py   # Offline PC rules (time, stats, apps, timers/alarms)
│   └── phone_adb.py     # (Slice 6) Android control via ADB over Wi-Fi/USB
├── brain/               # Slice 2: Cloud LLM routing & connectivity
│   ├── __init__.py
│   └── router.py        # Internet check + Groq -> Gemini fallback router
└── APP-UI/              # Slice 5: Cyan/blue holographic HUD overlay (HTML/CSS/JS -> Tauri)
    └── index.html       # Standalone HUD prototype (idle/listening/thinking/speaking)