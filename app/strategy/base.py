from abc import ABC, abstractmethod
from typing import List, Optional

from app.domain.entities import Candle, Signal


class Strategy(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @abstractmethod
    def compute_signal(self, candles: List[Candle]) -> Optional[Signal]:
        ...

    @abstractmethod
    def min_candles_required(self) -> int:
        ...
