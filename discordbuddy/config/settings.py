"""Structured configuration models powered by Pydantic."""

from pathlib import Path
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class HardwareConfig(BaseModel):
    """Target hardware and GPU execution settings."""

    gpu_name: str = "AMD Radeon RX 6700 XT 12GB"
    cpu_name: str = "Intel Core i5-12400F"
    n_gpu_layers: int = Field(default=33, description="GPU layers offloaded to Vulkan/DirectML")
    n_threads: int = Field(default=6, description="CPU threads for CPU execution tasks")
    use_vulkan: bool = Field(default=True, description="Enable Vulkan backend for AMD GPU")


class BrainConfig(BaseModel):
    """LLM configuration for conversation brain."""

    backend_type: str = Field(
        default="openai_api",
        description="Local LLM backend type: 'openai_api' (LM Studio/Ollama) or 'llama_cpp'",
    )
    api_base_url: str = Field(
        default="http://127.0.0.1:1234/v1",
        description="Local OpenAI-compatible API base URL (e.g. LM Studio 0.4.19, Ollama, vLLM)",
    )
    api_key: str = Field(default="lm-studio", description="API key if required by local server")
    model_name: str = Field(default="qwen3-14b-instruct", description="Model name or ID loaded in server")
    model_path: Path = Field(default=Path("models/qwen3_14b.gguf"), description="Local GGUF model file path")
    context_window: int = Field(default=4096, description="Context window size")
    temperature: float = Field(default=0.7, description="Sampling temperature")
    max_tokens: int = Field(default=100, description="Max token generation per response")
    repeat_penalty: float = Field(default=1.1, description="Repetition penalty")
    max_retries: int = Field(default=3, description="Maximum retries for local API connections")
    retry_delay: float = Field(default=1.0, description="Initial retry backoff delay in seconds")
    enable_diagnostic_check: bool = Field(
        default=True, description="Run startup diagnostic completion request against local LM Studio server"
    )


class VisionConfig(BaseModel):
    """VLM and screen capture configuration."""

    vlm_model_name: str = "Qwen2.5-VL-3B-Instruct-Q4_K_M.gguf"
    vlm_model_path: Path = Field(default=Path("models/qwen2.5_vl_3b.gguf"))
    capture_fps: int = Field(default=2, description="DXcam screen sampling FPS")
    frame_difference_threshold: float = Field(
        default=0.15, description="Pixel change threshold to trigger VLM inference"
    )
    vlm_inference_cooldown: float = Field(
        default=3.0, description="Minimum seconds between VLM calls"
    )


class AttentionConfig(BaseModel):
    """Attention engine & silence tracker configuration."""

    silence_timeout_seconds: float = Field(
        default=45.0, description="Seconds of total silence before considering spontaneous speak"
    )
    speaking_score_threshold: float = Field(
        default=0.6, description="Score threshold required for AI to speak"
    )
    spontaneous_cooldown_seconds: float = Field(
        default=60.0, description="Minimum delay between unprompted spontaneous comments"
    )


class MemoryConfig(BaseModel):
    """SQLite memory store configuration."""

    db_path: Path = Field(default=Path("data/discordbuddy_memory.db"))
    max_conversation_history: int = Field(default=20, description="History window length")
    enable_auto_summarization: bool = Field(default=True)


class VoiceConfig(BaseModel):
    """STT (faster-whisper) and TTS (Piper) configuration."""

    stt_model: str = Field(default="base.en", description="faster-whisper model size")
    stt_device: str = Field(default="cpu", description="STT device: cpu or cuda/directml")
    tts_voice: str = Field(default="en_US-lessac-medium", description="Piper TTS voice model")
    tts_model_path: Path = Field(default=Path("models/piper_voice.onnx"))
    sample_rate: int = Field(default=16000, description="Audio sample rate in Hz")
    mic_device_id: int | None = Field(default=None, description="Optional microphone device index")
    enable_tts_playback: bool = Field(default=True, description="Enable speaker audio playback")


class UIConfig(BaseModel):
    """Desktop PySide6 interface configuration."""

    show_tray_icon: bool = Field(default=True)
    start_minimized: bool = Field(default=False)
    overlay_enabled: bool = Field(default=True)
    interactive_console: bool = Field(default=False, description="Enable interactive terminal console mode")


from discordbuddy.core.types import InteractionMode


class Settings(BaseSettings):
    """Root configuration aggregator for DiscordBuddy."""

    app_name: str = "DiscordBuddy"
    environment: str = "development"
    log_level: str = "INFO"
    interaction_mode: InteractionMode = Field(default=InteractionMode.PASSIVE_DESKTOP, description="Active interaction mode")

    hardware: HardwareConfig = Field(default_factory=HardwareConfig)
    brain: BrainConfig = Field(default_factory=BrainConfig)
    vision: VisionConfig = Field(default_factory=VisionConfig)
    attention: AttentionConfig = Field(default_factory=AttentionConfig)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    voice: VoiceConfig = Field(default_factory=VoiceConfig)
    ui: UIConfig = Field(default_factory=UIConfig)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",
    )
