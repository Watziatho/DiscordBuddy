# DiscordBuddy 🎮🎧

> A 100% local, free, desktop AI companion for Windows 11 that behaves like a friend hanging out in a Discord voice call while watching your stream.

---

## Overview

**DiscordBuddy** is NOT an assistant, tutor, narrator, coach, or productivity agent. It's a friend who sits in voice chat with you while you game, browse, or code. It remains silent most of the time, making brief 3–12 word comments, jokes, or observations when interesting events occur on your screen or in conversation.

### Key Highlights
- **100% Offline & Private**: Zero runtime cloud calls. Runs entirely on local hardware.
- **Hardware Optimized**: Targets AMD Radeon RX 6700 XT 12GB VRAM & Intel i5-12400F CPU.
- **Vision Event-Driven**: Vision models process screenshots into semantic events (`BossAppeared`, `FunnyDeath`, `LargeExplosion`, etc.) instead of running heavy LLM inference constantly.
- **Attention Engine**: Intelligent silence tracker and turn-taking scoring matrix ensure the AI stays quiet unless an event warrants speaking.
- **Anti-ChatGPT Vibe**: Strictly enforced casual, concise, conversational tone without corporate fluff or ending every sentence with a question.
- **Long-Term Memory**: Persistent SQLite memory store tracks shared jokes, accomplishments, and game experiences over time.
- **Modular Plugin System**: Extensible architecture supporting game-specific telemetry plugins.

---

## Tech Stack

| Domain | Technology |
|---|---|
| **OS Target** | Windows 11 (Python 3.12+) |
| **LLM Runtime** | `llama.cpp` / `llama-cpp-python` |
| **Conversation Model** | Qwen3 14B Q4_K_M |
| **Vision Model** | Qwen2.5-VL 3B / 7B |
| **Screen Capture** | DXcam + OpenCV |
| **Speech-to-Text (STT)** | `faster-whisper` / `whisper.cpp` |
| **Text-to-Speech (TTS)** | Piper TTS |
| **Memory Store** | SQLite (`aiosqlite`) |
| **Desktop UI** | PySide6 |
| **Logging & Config** | `loguru` + `pydantic-settings` |

---

## Quick Start

### Prerequisites
- Windows 11
- Python 3.12 or higher
- AMD GPU driver supporting Vulkan or DirectML (for RX 6700 XT)

### Installation

```powershell
# Clone or navigate to directory
cd e:\Projects\DiscordBuddy

# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install package and dependencies
pip install -e .[dev]
```

### Running the Application

```powershell
# Run main entrypoint
python -m discordbuddy.main
```

### Running Unit Tests

```powershell
pytest
```

---

## Documentation

Detailed architectural and design specifications can be found in the `docs/` folder:

- [`docs/ARCHITECTURE.md`](file:///e:/Projects/DiscordBuddy/docs/ARCHITECTURE.md): Event bus design, pipeline flows, hardware resource budgets.
- [`docs/ANTI_CHATGPT.md`](file:///e:/Projects/DiscordBuddy/docs/ANTI_CHATGPT.md): Vibe guidelines, forbidden response patterns, and tone enforcement.
- [`docs/VISION.md`](file:///e:/Projects/DiscordBuddy/docs/VISION.md): DXcam screen capture engine, heuristic frame filtering, and VLM event extraction.
- [`docs/MEMORY.md`](file:///e:/Projects/DiscordBuddy/docs/MEMORY.md): Long-term memory schema, session tracking, and recall scoring.
- [`docs/PERSONALITY.md`](file:///e:/Projects/DiscordBuddy/docs/PERSONALITY.md): System prompts, emotion/vibe states, and comment length rules.
- [`docs/PLUGIN_API.md`](file:///e:/Projects/DiscordBuddy/docs/PLUGIN_API.md): Developing third-party game state plugins.
- [`docs/ROADMAP.md`](file:///e:/Projects/DiscordBuddy/docs/ROADMAP.md): Development phases and future features.

---

## License

MIT License. See LICENSE for details.
