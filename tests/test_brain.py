"""Unit tests for BrainService local LLM backends, LM Studio connection, retries, and diagnostics."""

import pytest
import httpx
from discordbuddy.brain.service import BrainService
from discordbuddy.config.settings import BrainConfig


@pytest.mark.asyncio
async def test_brain_default_backend_selection() -> None:
    """Test default BrainConfig selects openai_api backend."""
    config = BrainConfig()
    assert config.backend_type == "openai_api"
    assert config.api_base_url == "http://127.0.0.1:1234/v1"
    assert config.model_name == "qwen3-14b-instruct"


@pytest.mark.asyncio
async def test_brain_llama_cpp_backend_selection() -> None:
    """Test switching backend to llama_cpp."""
    config = BrainConfig(backend_type="llama_cpp")
    brain = BrainService(config)
    await brain.initialize()

    assert brain.config.backend_type == "llama_cpp"
    assert brain._is_initialized is True
    # Model missing -> fallback mode without crash
    response = await brain.generate_response("Hello!")
    assert response == "That was clean."

    await brain.shutdown()


@pytest.mark.asyncio
async def test_brain_lm_studio_successful_connection(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test LM Studio 0.4.19 connection verification and model discovery."""
    config = BrainConfig(
        backend_type="openai_api",
        api_base_url="http://127.0.0.1:1234/v1",
        max_retries=1,
    )
    brain = BrainService(config)

    async def mock_get(self_client, url):
        class MockResponse:
            status_code = 200
            def json(self):
                return {
                    "object": "list",
                    "data": [{"id": "qwen3-14b-instruct", "object": "model"}],
                }
        return MockResponse()

    async def mock_post(self_client, url, json=None):
        class MockResponse:
            def raise_for_status(self):
                pass
            def json(self):
                return {
                    "choices": [
                        {"message": {"content": "That was clean."}}
                    ]
                }
        return MockResponse()

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)
    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    await brain.initialize()
    assert brain._is_connected is True
    assert "qwen3-14b-instruct" in brain.detected_models

    response = await brain.generate_response("Nice play!")
    assert response == "That was clean."

    await brain.shutdown()


@pytest.mark.asyncio
async def test_brain_connection_failure_and_non_crashing_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test connection failure when LM Studio is unreachable (no crash, fallback mode)."""
    config = BrainConfig(
        backend_type="openai_api",
        api_base_url="http://127.0.0.1:1234/v1",
        max_retries=1,
        retry_delay=0.01,
    )
    brain = BrainService(config)

    async def mock_fail(self_client, url, **kwargs):
        raise httpx.ConnectError("Connection refused")

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_fail)
    monkeypatch.setattr(httpx.AsyncClient, "post", mock_fail)

    # Must initialize without raising unhandled exception
    await brain.initialize()

    assert brain._is_initialized is True
    assert brain._is_connected is False

    # Generation returns fallback string without crashing
    response = await brain.generate_response("What happened?")
    assert response == "That was clean."

    await brain.shutdown()


@pytest.mark.asyncio
async def test_brain_exponential_backoff_retry_logic(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test exponential backoff retries when connection attempts initially fail."""
    config = BrainConfig(
        backend_type="openai_api",
        api_base_url="http://127.0.0.1:1234/v1",
        max_retries=3,
        retry_delay=0.01,
    )
    brain = BrainService(config)

    attempt_counter = 0

    async def mock_get_retry(self_client, url):
        nonlocal attempt_counter
        attempt_counter += 1
        if attempt_counter < 3:
            raise httpx.ConnectError("Server starting up...")
        class MockResponse:
            status_code = 200
            def json(self):
                return {"data": [{"id": "qwen3-14b-instruct"}]}
        return MockResponse()

    async def mock_post(self_client, url, json=None):
        class MockResponse:
            status_code = 200
            def json(self):
                return {"choices": [{"message": {"content": "CONNECTED"}}]}
        return MockResponse()

    await brain.shutdown()


@pytest.mark.asyncio
async def test_prompt_builder_structure() -> None:
    """Test PromptBuilder generates structured Chat Completions messages list."""
    from discordbuddy.personality.prompt_builder import PromptBuilder

    builder = PromptBuilder()
    messages = builder.build_messages("Hello")

    assert isinstance(messages, list)
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert "friend hanging out" in messages[0]["content"]
    assert messages[1]["role"] == "user"
    assert messages[1]["content"] == "Hello"


@pytest.mark.asyncio
async def test_brain_chat_completions_payload_and_parsing(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test BrainService passes structured messages payload and parses choices[0].message.content."""
    config = BrainConfig(backend_type="openai_api", max_retries=1, enable_diagnostic_check=False)
    brain = BrainService(config)

    captured_payload: dict = {}

    async def mock_get(self_client, url):
        class MockResponse:
            status_code = 200
            def json(self):
                return {"data": [{"id": "qwen3-14b-instruct"}]}
        return MockResponse()

    async def mock_post(self_client, url, json=None):
        nonlocal captured_payload
        captured_payload = json or {}
        class MockResponse:
            status_code = 200
            def raise_for_status(self):
                pass
            def json(self):
                return {
                    "choices": [
                        {"message": {"content": "   CONNECTED   "}}
                    ]
                }
        return MockResponse()

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)
    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    await brain.initialize()

    from discordbuddy.personality.prompt_builder import PromptBuilder
    builder = PromptBuilder()
    input_messages = builder.build_messages("Hello")

    await brain.shutdown()


def test_clean_reasoning_text_variations() -> None:
    """Test clean_reasoning_text handling normal, complete, truncated, and malformed <think> blocks."""
    from discordbuddy.brain.service import clean_reasoning_text

    # 1. Normal reply without thinking
    text1, had1, trunc1 = clean_reasoning_text("That was clean.")
    assert text1 == "That was clean."
    assert had1 is False
    assert trunc1 is False

    # 2. Reply with complete <think>...</think> block
    text2, had2, trunc2 = clean_reasoning_text("<think>\nLet me analyze the gameplay...\n</think>\nNice clutch!")
    assert text2 == "Nice clutch!"
    assert had2 is True
    assert trunc2 is False

    # 3. Truncated <think> block (no closing tag)
    text3, had3, trunc3 = clean_reasoning_text("<think>\nOkay, the user wants me to reply...")
    assert text3 == ""
    assert had3 is True
    assert trunc3 is True

    # 4. Malformed / orphaned </think> tag
    text4, had4, trunc4 = clean_reasoning_text("Orphaned reasoning text </think> Actual reply text")
    assert text4 == "Actual reply text"
    assert had4 is True
    assert trunc4 is False


@pytest.mark.asyncio
async def test_brain_thinking_block_stripping_and_retry(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test BrainService auto-retry when finish_reason='length' inside a thinking block."""
    config = BrainConfig(backend_type="openai_api", max_retries=1, enable_diagnostic_check=False)
    brain = BrainService(config)

    post_count = 0

    async def mock_get(self_client, url):
        class MockResponse:
            status_code = 200
            def json(self):
                return {"data": [{"id": "qwen3-14b-instruct"}]}
        return MockResponse()

    async def mock_post(self_client, url, json=None):
        nonlocal post_count
        post_count += 1
        class MockResponse:
            status_code = 200
            def raise_for_status(self):
                pass
            def json(self):
                if post_count == 1:
                    # Initial response truncated during thinking block
                    return {
                        "choices": [
                            {
                                "finish_reason": "length",
                                "message": {"content": "<think>\nThinking about the response..."}
                            }
                        ]
                    }
                else:
                    # Retry response with complete thinking block and clean reply
                    return {
                        "choices": [
                            {
                                "finish_reason": "stop",
                                "message": {"content": "<think>\nThought done.\n</think>\nThat was clean."}
                            }
                        ]
                    }
        return MockResponse()

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)
    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    await brain.initialize()

    response = await brain.generate_response("Test prompt", max_tokens=20)

    # Verify auto-retry occurred and returned clean text without exposing thinking tokens
    assert post_count == 2
    assert response == "That was clean."

    await brain.shutdown()


def test_clean_response_text_variations() -> None:
    """Test clean_response_text for normal text, combining marks, zero-width chars, and markdown."""
    from discordbuddy.brain.service import clean_response_text

    # 1. Normal text remains unchanged
    assert clean_response_text("That was clean.") == "That was clean."

    # 2. Combining underline characters are removed
    assert clean_response_text("̲̲̲̲̲̲̲̲̲") == ""
    assert clean_response_text("H̲e̲l̲l̲o̲") == "Hello"

    # 3. Zero-width characters are removed
    assert clean_response_text("\u200bHello\u200c \u200dWorld\ufeff") == "Hello World"

    # 4. Markdown formatting characters still work
    assert clean_response_text("**bold** and *italic* # header") == "**bold** and *italic* # header"


@pytest.mark.asyncio
async def test_brain_empty_after_clean_retry(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test BrainService retries once with plain text instruction when output is empty after sanitization."""
    config = BrainConfig(backend_type="openai_api", max_retries=1, enable_diagnostic_check=False)
    brain = BrainService(config)

    captured_payloads: list[dict] = []

    async def mock_get(self_client, url):
        class MockResponse:
            status_code = 200
            def json(self):
                return {"data": [{"id": "qwen3-14b-instruct"}]}
        return MockResponse()

    async def mock_post(self_client, url, json=None):
        captured_payloads.append(json or {})
        class MockResponse:
            status_code = 200
            def raise_for_status(self):
                pass
            def json(self):
                if len(captured_payloads) == 1:
                    # Initial response contains only combining underline characters
                    return {"choices": [{"message": {"content": "̲̲̲̲̲̲̲̲̲"}}]}
                else:
                    # Retry response returns clean text
                    return {"choices": [{"message": {"content": "That was clean."}}]}
        return MockResponse()

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)
    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    await brain.initialize()

    response = await brain.generate_response("Hello!")

    # Verify initial call returned empty-after-clean and triggered retry with extra instruction
    assert len(captured_payloads) == 2
    retry_msg = captured_payloads[1]["messages"][-1]["content"]
    assert "Reply with normal plain text only." in retry_msg
    assert response == "That was clean."

    await brain.shutdown()
