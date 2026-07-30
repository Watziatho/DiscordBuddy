"""Implementation of IBrain supporting OpenAI-compatible local APIs (LM Studio 0.4.19/Ollama) and llama.cpp."""

import asyncio
import json
import time
import unicodedata
from typing import Any, AsyncGenerator
import httpx
from loguru import logger
from discordbuddy.config.settings import BrainConfig
from discordbuddy.interfaces.brain import IBrain

ZERO_WIDTH_CHARS = {"\u200b", "\u200c", "\u200d", "\ufeff"}


def clean_response_text(content: str) -> str:
    """Sanitize LLM output by removing zero-width characters and Unicode combining marks (Mn category).

    Args:
        content: Raw or reasoning-stripped response text.

    Returns:
        Sanitized plain response string.
    """
    if not content:
        return ""

    cleaned_chars = []
    for char in content:
        if char in ZERO_WIDTH_CHARS:
            continue
        if unicodedata.category(char) == "Mn":
            continue
        cleaned_chars.append(char)

    return "".join(cleaned_chars).strip()


def clean_reasoning_text(content: str) -> tuple[str, bool, bool]:
    """Safely parse and remove <think>...</think> reasoning blocks from model content.

    Args:
        content: Raw text returned by LLM.

    Returns:
        tuple[str, bool, bool]: (cleaned_text, had_reasoning, is_unterminated_thinking)
    """
    if not content:
        return "", False, False

    text = content.strip()
    had_reasoning = False
    is_unterminated_thinking = False

    # Process complete <think>...</think> blocks
    while "<think>" in text:
        had_reasoning = True
        start_idx = text.find("<think>")
        end_idx = text.find("</think>", start_idx)

        if end_idx != -1:
            # Complete <think>...</think> block found
            text = text[:start_idx] + text[end_idx + len("</think>"):]
        else:
            # Unterminated <think> block (no closing </think>)
            is_unterminated_thinking = True
            text = text[:start_idx]
            break

    # Handle orphaned </think> tag without matching opening <think>
    if "</think>" in text:
        had_reasoning = True
        end_idx = text.find("</think>")
        text = text[end_idx + len("</think>"):]

    cleaned = text.strip()
    return cleaned, had_reasoning, is_unterminated_thinking


class BrainService(IBrain):
    """Local LLM brain service supporting OpenAI-compatible local endpoints and llama.cpp."""

    def __init__(self, config: BrainConfig) -> None:
        self.config = config
        self._is_initialized: bool = False
        self._is_connected: bool = False
        self._llama_instance: Any = None
        self._http_client: httpx.AsyncClient | None = None
        self.detected_models: list[str] = []
        self.last_diagnostic_raw_response: dict[str, Any] | None = None
        self.last_diagnostic_parsed_response: str | None = None

    async def initialize(self) -> None:
        """Initialize brain service based on backend type and print startup diagnostics."""
        backend = self.config.backend_type.lower()

        logger.info("=== BrainService Startup Diagnostics ===")
        logger.info(f"Backend Selected  : {backend}")
        logger.info(f"Base URL          : {self.config.api_base_url}")
        logger.info(f"Configured Model  : {self.config.model_name}")

        if backend == "openai_api":
            await self._init_openai_api()
        elif backend == "llama_cpp":
            await self._init_llama_cpp()
        else:
            logger.warning(f"Unknown backend_type '{backend}'. Operating in fallback mode.")

        self._is_initialized = True
        logger.info(f"BrainService startup complete. Active status: {'CONNECTED' if self._is_connected else 'FALLBACK'}")

    async def _init_openai_api(self) -> None:
        """Initialize HTTP client targeting local OpenAI-compatible endpoint (LM Studio / Ollama)."""
        base_url = self.config.api_base_url
        if not base_url.endswith("/"):
            base_url += "/"

        self._http_client = httpx.AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"Bearer {self.config.api_key}"},
            timeout=30.0,
        )

        # 1. Verify connection and model list
        connected = await self._verify_connection_with_retry()
        self._is_connected = connected

        # Check if configured model is available
        if connected:
            if self.config.model_name in self.detected_models:
                logger.info(f"Verified target model '{self.config.model_name}' is loaded on LM Studio server.")
            else:
                logger.warning(
                    f"Configured model '{self.config.model_name}' not explicitly listed in server models: {self.detected_models}"
                )

        # 2. Run single diagnostic completion request if enabled
        if connected and self.config.enable_diagnostic_check:
            await self._run_diagnostic_check()

    async def _verify_connection_with_retry(self) -> bool:
        """Ping local server models endpoint with exponential backoff retries."""
        assert self._http_client is not None
        max_retries = max(1, self.config.max_retries)
        delay = max(0.1, self.config.retry_delay)

        for attempt in range(1, max_retries + 1):
            try:
                logger.debug(f"Attempting API connection to LM Studio/OpenAI server (Attempt {attempt}/{max_retries})...")
                response = await self._http_client.get("models")
                if response.status_code == 200:
                    data = response.json()
                    raw_models = data.get("data", [])
                    self.detected_models = [
                        m.get("id", "") for m in raw_models if isinstance(m, dict) and "id" in m
                    ]

                    logger.info("=== LM Studio / Local OpenAI API Connection Verified ===")
                    logger.info(f"API Connection Status : SUCCESS (HTTP {response.status_code})")
                    logger.info(f"Detected Models       : {self.detected_models if self.detected_models else 'None reported'}")
                    return True
                else:
                    logger.warning(f"API ping returned non-200 status code: HTTP {response.status_code}")
            except (httpx.RequestError, httpx.HTTPStatusError) as exc:
                logger.warning(
                    f"Connection attempt {attempt}/{max_retries} failed for '{self.config.api_base_url}': {exc}"
                )

            if attempt < max_retries:
                backoff = delay * (2 ** (attempt - 1))
                logger.debug(f"Retrying connection in {backoff:.1f} seconds...")
                await asyncio.sleep(backoff)

        logger.error(
            f"ERROR: Failed to connect to local OpenAI-compatible inference server at '{self.config.api_base_url}' "
            f"after {max_retries} attempts. Please verify LM Studio 0.4.19 is running."
        )
        logger.info("API Connection Status : FAILED (Application will run in fallback mode without crashing)")
        return False

    async def _run_diagnostic_check(self) -> None:
        """Run single startup diagnostic completion request against LM Studio using Chat Completions messages format."""
        assert self._http_client is not None
        messages = [
            {"role": "system", "content": "You are DiscordBuddy."},
            {"role": "user", "content": "Reply with exactly: CONNECTED"},
        ]

        payload = {
            "model": self.config.model_name,
            "messages": messages,
            "temperature": 0.0,
            "max_tokens": 150,
            "reasoning_effort": "none",
        }

        logger.info("=== Running Startup End-to-End Diagnostic Request ===")
        logger.info(f"Request sent          : POST chat/completions (Model: '{self.config.model_name}')")
        logger.info(f"Diagnostic Payload   : {json.dumps(messages)}")

        start_time = time.perf_counter()
        max_retries = max(1, self.config.max_retries)

        for attempt in range(1, max_retries + 1):
            try:
                response = await self._http_client.post("chat/completions", json=payload)
                elapsed_time = time.perf_counter() - start_time

                if response.status_code == 200:
                    data = response.json()
                    self.last_diagnostic_raw_response = data

                    # Extract choices[0].message.content with clean_reasoning_text and clean_response_text
                    choices = data.get("choices", [])
                    parsed_content = ""
                    if choices and isinstance(choices[0], dict):
                        finish_reason = choices[0].get("finish_reason")
                        message = choices[0].get("message", {})
                        if isinstance(message, dict):
                            raw_content = message.get("content", "").strip()
                            reasoning_cleaned, had_reasoning, is_unterminated = clean_reasoning_text(raw_content)

                            if is_unterminated and finish_reason == "length" and payload["max_tokens"] < 300:
                                logger.info("Diagnostic check truncated during thinking block. Retrying with max_tokens=300...")
                                payload["max_tokens"] = 300
                                continue

                            parsed_content = clean_response_text(reasoning_cleaned)

                            if had_reasoning:
                                logger.debug(
                                    f"Stripped <think> reasoning block from diagnostic response "
                                    f"(Original len: {len(raw_content)} -> Cleaned len: {len(parsed_content)})"
                                )

                    self.last_diagnostic_parsed_response = parsed_content

                    logger.info(f"Total response time   : {elapsed_time:.3f} seconds")
                    logger.info(f"Time to first token   : ~{elapsed_time:.3f} seconds (non-streaming)")
                    logger.info(f"Raw API Response      : {json.dumps(data, indent=2)}")
                    logger.info(f"Parsed Assistant Text : '{parsed_content}'")

                    print("\n====================================")
                    print("Brain connection successful")
                    print("====================================\n")
                    return
                else:
                    logger.error(f"Diagnostic request failed (HTTP {response.status_code})")
                    logger.error(f"Response Body: {response.text}")
                    logger.error(f"Attempt: {attempt}/{max_retries}")
            except Exception as exc:
                logger.error(f"Diagnostic request exception on attempt {attempt}/{max_retries}: {exc}")

            if attempt < max_retries:
                await asyncio.sleep(self.config.retry_delay)

        logger.warning("Diagnostic check did not receive expected response. Continuing application execution without crashing.")

    async def _init_llama_cpp(self) -> None:
        """Initialize in-process llama.cpp model."""
        if not self.config.model_path.exists():
            logger.warning(
                f"llama.cpp GGUF model file not found at '{self.config.model_path}'. "
                "BrainService will operate in fallback mode until model is downloaded."
            )
            return

        try:
            import llama_cpp  # type: ignore[import-untyped]

            loop = asyncio.get_running_loop()
            self._llama_instance = await loop.run_in_executor(
                None,
                lambda: llama_cpp.Llama(
                    model_path=str(self.config.model_path),
                    n_ctx=self.config.context_window,
                    verbose=False,
                ),
            )
            self._is_connected = True
            logger.info("llama.cpp model loaded successfully into memory.")
        except ImportError:
            logger.warning("llama_cpp Python package not installed. Running in fallback mode.")
        except Exception as exc:
            logger.error(f"Failed to load llama.cpp model: {exc}")

    async def generate_response(
        self,
        prompt: str | list[dict[str, str]],
        system_prompt: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> str:
        """Generate response string from configured local backend using structured messages."""
        if not self._is_initialized:
            raise RuntimeError("BrainService must be initialized before generating responses.")

        max_tok = max_tokens if max_tokens is not None else self.config.max_tokens
        temp = temperature if temperature is not None else self.config.temperature

        # Normalize input prompt into structured messages list
        if isinstance(prompt, list):
            messages = prompt
        else:
            sys_prompt = system_prompt or "You are a friend hanging out in voice chat."
            messages = [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": prompt},
            ]

        backend = self.config.backend_type.lower()
        logger.debug(f"Generating response using backend '{backend}' ({len(messages)} messages)...")

        if backend == "openai_api" and self._http_client:
            return await self._generate_openai_api(messages, max_tok, temp)
        elif backend == "llama_cpp" and self._llama_instance:
            return await self._generate_llama_cpp(messages, max_tok, temp)

        # Fallback response if model file / endpoint is unavailable
        return "That was clean."

    async def _generate_openai_api(
        self,
        messages: list[dict[str, str]],
        max_tokens: int,
        temperature: float,
        is_retry: bool = False,
        is_empty_retry: bool = False,
    ) -> str:
        """Call local OpenAI-compatible chat completions endpoint with retry and reasoning/Unicode removal."""
        assert self._http_client is not None
        payload = {
            "model": self.config.model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "reasoning_effort": "none",
        }

        max_retries = max(1, self.config.max_retries)
        delay = max(0.1, self.config.retry_delay)

        for attempt in range(1, max_retries + 1):
            try:
                response = await self._http_client.post("chat/completions", json=payload)
                response.raise_for_status()
                data = response.json()
                choices = data.get("choices", [])
                if choices and isinstance(choices[0], dict):
                    finish_reason = choices[0].get("finish_reason")
                    message = choices[0].get("message", {})
                    if isinstance(message, dict):
                        raw_content = message.get("content", "").strip()

                        # Step 1: Strip <think> reasoning tags
                        reasoning_cleaned, had_reasoning, is_unterminated = clean_reasoning_text(raw_content)

                        if had_reasoning:
                            logger.debug(
                                f"Stripped <think> reasoning block from response "
                                f"(Original len: {len(raw_content)} -> Cleaned len: {len(reasoning_cleaned)})"
                            )

                        # Retry if truncated inside thinking block
                        if is_unterminated and finish_reason == "length" and not is_retry:
                            logger.info(
                                "Response truncated during thinking block (finish_reason='length'). "
                                "Retrying with larger max_tokens (300)..."
                            )
                            return await self._generate_openai_api(
                                messages=messages,
                                max_tokens=max(300, max_tokens * 3),
                                temperature=temperature,
                                is_retry=True,
                                is_empty_retry=is_empty_retry,
                            )

                        # Step 2: Remove zero-width characters and Mn combining marks
                        cleaned = clean_response_text(reasoning_cleaned)

                        # Step 3: Handle empty-after-clean by retrying with plain text instruction
                        if len(cleaned) < 1:
                            if not is_empty_retry:
                                logger.warning(
                                    "LLM response was empty or contained only invalid combining/zero-width characters. "
                                    "Retrying with plain text instruction..."
                                )
                                retry_messages = list(messages)
                                retry_messages.append(
                                    {
                                        "role": "user",
                                        "content": "Reply with normal plain text only. Do not use formatting characters.",
                                    }
                                )
                                return await self._generate_openai_api(
                                    messages=retry_messages,
                                    max_tokens=max_tokens,
                                    temperature=temperature,
                                    is_retry=is_retry,
                                    is_empty_retry=True,
                                )
                            else:
                                logger.error("LLM response remained empty after retry with plain text instruction.")
                                return "That was clean."

                        logger.debug(f"Received OpenAI API response: '{cleaned}'")
                        return cleaned
            except Exception as exc:
                logger.warning(
                    f"OpenAI API request attempt {attempt}/{max_retries} failed for '{self.config.api_base_url}': {exc}"
                )
                if attempt < max_retries:
                    backoff = delay * (2 ** (attempt - 1))
                    await asyncio.sleep(backoff)

        logger.error(
            f"OpenAI API request failed after {max_retries} retries. Falling back to default response."
        )
        return "That was clean."

    async def _generate_llama_cpp(
        self,
        messages: list[dict[str, str]],
        max_tokens: int,
        temperature: float,
    ) -> str:
        """Run in-process llama.cpp inference via Chat Completions format."""
        assert self._llama_instance is not None
        loop = asyncio.get_running_loop()

        def _infer() -> str:
            raw_text = ""
            if hasattr(self._llama_instance, "create_chat_completion"):
                output = self._llama_instance.create_chat_completion(
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
                choices = output.get("choices", [])
                if choices and isinstance(choices[0], dict):
                    message = choices[0].get("message", {})
                    if isinstance(message, dict):
                        raw_text = message.get("content", "").strip()
            else:
                prompt_str = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
                output = self._llama_instance(
                    prompt_str,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
                raw_text = output["choices"][0]["text"].strip()

            reasoning_cleaned, had_reasoning, _ = clean_reasoning_text(raw_text)
            if had_reasoning:
                logger.debug(
                    f"Stripped <think> reasoning block from llama.cpp response "
                    f"(Original len: {len(raw_text)} -> Cleaned len: {len(reasoning_cleaned)})"
                )
            cleaned = clean_response_text(reasoning_cleaned)
            return cleaned or "That was clean."

        try:
            return await loop.run_in_executor(None, _infer)
        except Exception as exc:
            logger.error(f"llama.cpp inference error: {exc}")
            return "That was clean."

    async def generate_stream(
        self,
        prompt: str | list[dict[str, str]],
        system_prompt: str | None = None,
        max_tokens: int = 100,
    ) -> AsyncGenerator[str, None]:
        """Stream generated response tokens asynchronously."""
        full_text = await self.generate_response(prompt, system_prompt, max_tokens)
        words = full_text.split()
        for i, word in enumerate(words):
            suffix = " " if i < len(words) - 1 else ""
            yield word + suffix

    async def shutdown(self) -> None:
        """Unload local model and close HTTP client."""
        logger.info("Shutting down BrainService.")
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None
        self._llama_instance = None
        self._is_initialized = False
        self._is_connected = False
