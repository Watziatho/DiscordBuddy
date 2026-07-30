"""Unit tests for the AttentionEngine decision scoring matrix."""

import pytest
from discordbuddy.attention.engine import AttentionEngine
from discordbuddy.config.settings import AttentionConfig
from discordbuddy.core.events import BossAppearedEvent, UserSpokeEvent


@pytest.mark.asyncio
async def test_attention_direct_question_always_speaks() -> None:
    """Test that direct questions from user always trigger speak decision."""
    engine = AttentionEngine(AttentionConfig())
    event = UserSpokeEvent(
        source="test",
        transcript="What weapon is that?",
        is_direct_question=True,
    )

    should_speak = await engine.evaluate_event(event)
    assert should_speak is True


@pytest.mark.asyncio
async def test_attention_high_score_event() -> None:
    """Test high priority boss appeared event triggers speak decision."""
    engine = AttentionEngine(AttentionConfig(speaking_score_threshold=0.5))
    event = BossAppearedEvent(
        source="test",
        description="Boss spawned",
    )

    should_speak = await engine.evaluate_event(event)
    assert should_speak is True
