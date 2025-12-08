from abc import ABC, abstractmethod
from typing import ClassVar


class Measure(ABC):
    display_name: ClassVar[str]

    @property
    @abstractmethod
    def measure_name(self) -> str:
        pass
