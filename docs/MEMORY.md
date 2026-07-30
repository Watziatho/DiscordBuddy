# DiscordBuddy Memory System Architecture

## Overview

The Memory system in **DiscordBuddy** gives the companion long-term continuity. It allows the AI to remember past shared experiences, inside jokes, game victories, funny fails, and favorite games over time across multiple gaming sessions.

Memory is implemented using **SQLite** (`aiosqlite` in Python) for fast, lightweight, 100% local persistent storage on Windows 11.

---

## SQLite Database Schema

The database resides at `data/discordbuddy_memory.db`.

```sql
-- Sessions Table: Tracks gaming/chat sessions
CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    primary_game TEXT,
    summary TEXT
);

-- Event Logs Table: Raw history of events
CREATE TABLE IF NOT EXISTS event_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT WARNING,
    timestamp TIMESTAMP NOT NULL,
    event_type TEXT NOT NULL,
    source TEXT NOT NULL,
    payload JSON NOT NULL,
    FOREIGN KEY(session_id) REFERENCES sessions(session_id)
);

-- Long-Term Memories Table: Distilled facts and memories
CREATE TABLE IF NOT EXISTS long_term_memories (
    memory_id TEXT PRIMARY KEY,
    created_at TIMESTAMP NOT NULL,
    category TEXT NOT NULL, -- e.g. 'inside_joke', 'game_accomplishment', 'preference', 'running_gag'
    content TEXT NOT NULL,
    importance_score REAL DEFAULT 1.0,
    last_recalled_at TIMESTAMP,
    recall_count INTEGER DEFAULT 0
);

-- Conversation History Table
CREATE TABLE IF NOT EXISTS conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    speaker TEXT NOT NULL, -- 'user' or 'ai'
    message TEXT NOT NULL,
    context_tags TEXT,
    FOREIGN KEY(session_id) REFERENCES sessions(session_id)
);
```

---

## Memory Retrieval Pipeline

1. **Trigger Event**: Vision or Speech event occurs (e.g. `BossAppeared` for `Elden Ring`).
2. **Context Query**: Memory module queries `long_term_memories` for matching tags/categories (e.g. past attempts against this boss).
3. **Relevance Scoring**:
   $$\text{Score} = \text{Similarity} \times \text{Importance} \times e^{-\lambda \Delta t}$$
4. **Context Injection**: Top 1–2 relevant memories are injected into the LLM system prompt as short background context (e.g., *"Context: User died to Malenia 14 times last Tuesday."*).

---

## Memory Consolidation (Post-Session)

When a session ends:
- A background task summarizes the session's key moments.
- High-importance events (e.g., boss defeated after 20 tries) are saved into `long_term_memories`.
- Older low-importance logs are pruned to keep the database fast and small (< 50MB).
