# DiscordBuddy Development Roadmap

## Phase 1: Architecture & Skeleton (Completed)
- [x] Complete project folder structure
- [x] `pyproject.toml` and requirement specifications
- [x] Pydantic configuration & Loguru logging framework
- [x] Asynchronous `EventBus` engine & event model definitions
- [x] Abstract module interfaces (`IBrain`, `IVision`, `IAttentionEngine`, etc.)
- [x] Comprehensive architectural documentation
- [x] Basic unit test suite scaffolding

## Phase 2: Local Voice Conversation MVP (Milestone 1 Completed)
- [x] Configurable local LLM brain (`llama.cpp` + local OpenAI-compatible APIs e.g. LM Studio / Ollama)
- [x] VoicePipeline audio STT event loop (`UserSpokeEvent`) & Piper TTS synthesis/playback (`AISpokeEvent`)
- [x] Anti-ChatGPT prompt layer & length sanitizer (3–12 words default)
- [x] ConversationManager coordinator linking EventBus, Attention, Memory, Brain, and Voice
- [ ] Implement DXcam screen capture engine & OpenCV frame difference filter
- [ ] Implement Qwen2.5-VL 3B/7B vision event extraction worker
- [ ] Implement `aiosqlite` memory store with full schema migrations

## Phase 3: Attention Engine & Vibe Tuning
- [x] Attention matrix scoring implementation with dynamic thresholding
- [x] Anti-ChatGPT prompt template engine & word length validator (3–12 words)
- [ ] Silence timeout trigger loop & anti-spam cooldowns
- [ ] Emotion state machine integration

## Phase 4: Desktop UI & System Integration
- [ ] PySide6 system tray application & floating voice avatar overlay
- [ ] Settings panel for audio input/output device selection and model path selection
- [ ] Real-time event log viewer GUI
- [ ] Hotkey controls (Mute, Force Talk, Clear Memory)

## Phase 5: Game Plugins & Community Features
- [ ] CS2 Game State Integration (GSI) plugin
- [ ] Minecraft Telemetry plugin
- [ ] Elden Ring / Dark Souls Boss health bar reader plugin
- [ ] Plugin installer & Marketplace interface
