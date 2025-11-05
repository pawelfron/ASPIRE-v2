from abc import ABC, abstractmethod


class Result(ABC):
    """Base class for analysis resutls."""

    @abstractmethod
    def serialize(self) -> dict:
        """Convert to JSON-serializable format."""
