"""
Base class for cleanup engines.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict


class CleanupEngineBase(ABC):
    """Abstract base class for text cleanup engines."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    @abstractmethod
    def clean(self, text: str, mode: str = "standard") -> str:
        """
        Clean text according to the specified mode.

        Args:
            text: Input text to clean
            mode: Cleanup mode ("conservative", "standard", "rewrite")

        Returns:
            Cleaned text
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the engine is available and ready."""
        pass

    def get_status(self) -> str:
        """Get status description of the engine."""
        return "Available" if self.is_available() else "Unavailable"
