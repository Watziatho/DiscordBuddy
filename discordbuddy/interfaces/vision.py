"""Abstract interface for DXcam screen capture and VLM event extraction."""

from abc import ABC, abstractmethod
from typing import Any
from discordbuddy.core.events import VisionEvent


class IVision(ABC):
    """Interface for DXcam screen capture and visual event processing."""

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize DXcam screen grabber and load local VLM model."""
        pass

    @abstractmethod
    async def start_capture(self) -> None:
        """Start the continuous screen capture and event filtering worker loop."""
        pass

    @abstractmethod
    async def stop_capture(self) -> None:
        """Stop screen capture loop."""
        pass

    @abstractmethod
    async def capture_frame(self) -> Any:
        """Capture a single frame from DXcam as an OpenCV/Numpy array."""
        pass

    @abstractmethod
    async def analyze_frame(self, frame: Any) -> VisionEvent | None:
        """Analyze a frame via Qwen2.5-VL to extract a high-level visual event.

        Args:
            frame: Numpy/OpenCV image array.

        Returns:
            Extracted VisionEvent instance or None if nothing noteworthy.
        """
        pass

    @abstractmethod
    async def shutdown(self) -> None:
        """Clean up DXcam resources and unload VLM model."""
        pass
