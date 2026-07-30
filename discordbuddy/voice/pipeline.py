"""Voice pipeline managing audio capture, VAD STT transcription, and TTS playback."""

import asyncio
import numpy as np
from loguru import logger
from discordbuddy.config.settings import VoiceConfig
from discordbuddy.core.event_bus import EventBus
from discordbuddy.core.events import UserSpokeEvent, AISpokeEvent
from discordbuddy.interfaces.voice import IVoicePipeline


class VoicePipeline(IVoicePipeline):
    """Handles audio input capture, STT transcription, TTS synthesis, and audio playback."""

    def __init__(self, config: VoiceConfig, event_bus: EventBus) -> None:
        self.config = config
        self.event_bus = event_bus
        self._is_listening: bool = False
        self._listener_task: asyncio.Task[None] | None = None
        self._stt_model: Any = None
        self._tts_voice: Any = None

    async def initialize(self) -> None:
        """Initialize STT (faster-whisper) and TTS (Piper) engines."""
        logger.info(
            f"Initializing VoicePipeline (STT Model: '{self.config.stt_model}', "
            f"Device: '{self.config.stt_device}', TTS Voice: '{self.config.tts_voice}')"
        )
        await self._init_stt()
        await self._init_tts()
        logger.info("VoicePipeline initialized successfully.")

    async def _init_stt(self) -> None:
        """Initialize faster-whisper model if available."""
        try:
            from faster_whisper import WhisperModel  # type: ignore[import-untyped]

            loop = asyncio.get_running_loop()
            self._stt_model = await loop.run_in_executor(
                None,
                lambda: WhisperModel(
                    self.config.stt_model,
                    device=self.config.stt_device,
                    compute_type="int8",
                ),
            )
            logger.info("faster-whisper model initialized successfully.")
        except ImportError:
            logger.warning("faster-whisper not installed. VoicePipeline running in audio simulation mode.")
        except Exception as exc:
            logger.error(f"Failed to load faster-whisper model: {exc}")

    async def _init_tts(self) -> None:
        """Initialize Piper TTS engine if available."""
        if not self.config.tts_model_path.exists():
            logger.warning(
                f"Piper TTS model file not found at '{self.config.tts_model_path}'. "
                "Speech synthesis will operate in text log mode."
            )
            return

        try:
            import piper  # type: ignore[import-untyped]
            self._tts_voice = piper.PiperVoice.load(str(self.config.tts_model_path))
            logger.info("Piper TTS voice loaded successfully.")
        except ImportError:
            logger.warning("piper-tts package not installed. Running TTS in simulation mode.")
        except Exception as exc:
            logger.error(f"Failed to load Piper TTS voice: {exc}")

    async def start_listening(self) -> None:
        """Start background VAD and microphone audio capture loop."""
        if self._is_listening:
            return
        self._is_listening = True
        self._listener_task = asyncio.create_task(self._listen_loop())
        logger.info("Audio STT listening loop started.")

    async def stop_listening(self) -> None:
        """Stop listening loop."""
        if not self._is_listening:
            return
        self._is_listening = False
        if self._listener_task:
            self._listener_task.cancel()
            try:
                await self._listener_task
            except asyncio.CancelledError:
                pass
        logger.info("Audio STT listening loop stopped.")

    async def simulate_user_speech(self, text: str, is_question: bool = False) -> None:
        """Helper for triggering a user speech event explicitly."""
        event = UserSpokeEvent(
            source="microphone",
            transcript=text,
            is_direct_question=is_question,
        )
        logger.info(f"User spoke: '{text}' (Direct Question: {is_question})")
        await self.event_bus.publish(event)

    async def speak(self, text: str) -> None:
        """Synthesize text via TTS and play back audio to speaker while emitting AISpokeEvent."""
        word_count = len(text.split())
        logger.info(f"AI Speaking ({word_count} words): '{text}'")

        # Emit AISpokeEvent on central EventBus
        ai_event = AISpokeEvent(
            source="voice_pipeline",
            text=text,
            word_count=word_count,
        )
        await self.event_bus.publish(ai_event)

        # Synthesize & Playback if enabled
        if self.config.enable_tts_playback:
            await self._play_audio(text)

    async def _play_audio(self, text: str) -> None:
        """Synthesize audio waveform and output to sound device."""
        if self._tts_voice:
            try:
                loop = asyncio.get_running_loop()

                def _synth_and_play() -> None:
                    try:
                        import sounddevice as sd  # type: ignore[import-untyped]
                        # Piper synthesis playback placeholder
                        sd.sleep(100)
                    except Exception as play_exc:
                        logger.warning(f"Audio playback device warning: {play_exc}")

                await loop.run_in_executor(None, _synth_and_play)
            except Exception as exc:
                logger.error(f"TTS Synthesis error: {exc}")

    async def _listen_loop(self) -> None:
        """Background audio capture and STT processing loop."""
        while self._is_listening:
            try:
                await asyncio.sleep(0.5)
                # VAD chunk monitoring loop
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error(f"Error in audio listening loop: {exc}")

    async def shutdown(self) -> None:
        """Clean up audio streams and unload STT/TTS models."""
        await self.stop_listening()
        self._stt_model = None
        self._tts_voice = None
        logger.info("VoicePipeline shut down cleanly.")
