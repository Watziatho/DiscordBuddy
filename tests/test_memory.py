"""Unit tests for SQLite memory store operations."""

import pytest
from discordbuddy.config.settings import MemoryConfig
from discordbuddy.memory.store import MemoryStore


@pytest.mark.asyncio
async def test_memory_store_initialization(tmp_path) -> None:
    """Test memory store database connection and table creation."""
    db_file = tmp_path / "test_memory.db"
    config = MemoryConfig(db_path=db_file)
    store = MemoryStore(config)

    await store.initialize()
    assert store._is_connected is True

    await store.close()
    assert store._is_connected is False
