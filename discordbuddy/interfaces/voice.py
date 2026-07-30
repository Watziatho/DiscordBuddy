"""Abstract interface for Voice STT (faster-whisper) and TTS (Piper)."""

from abc import ABC, abstractmethod


class IVoicePipeline(ABC):
    """Interface for audio input listening (STT) and speech synthesis (TTS)."""

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize audio devices, load STT model, and load Piper TTS engine."""
        pass

    @abstractmethod
    async def start_listening(self) -> None:
        """Start background VAD and speech-to-text listener loop."""
        pass

    @abstractmethod
    async def stop_listening(self) -> None:
        """Stop listening loop."""
        pass

    @abstractmethod
    async def speak(self, text: str) -> None:
        """Synthesize text via Piper TTS and play back audio to virtual audio output.

        Args:
            text: Text to synthesize and speak.
        """
        pass

    @abstractmethod
    async def shutdown(self) -> None:
        """Clean up audio streams and unload TTS/STT engines."""
        pass
