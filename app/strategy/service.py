from typing import List, Optional

from app.core.logging import get_logger
from app.domain.entities import Candle, Signal
from app.strategy.base import Strategy

logger = get_logger(__name__)


class StrategyService:
    def __init__(self, strategy: Strategy) -> None:
        self._strategy = strategy

    def evaluate(self, candles: List[Candle]) -> Optional[Signal]:
        if len(candles) < self._strategy.min_candles_required():
            logger.warning(
                "insufficient_candles",
                strategy=self._strategy.name,
                required=self._strategy.min_candles_required(),
                got=len(candles),
            )
            return None

        signal = self._strategy.compute_signal(candles)
        if signal:
            logger.info(
                "signal_computed",
                strategy=self._strategy.name,
                symbol=signal.symbol,
                action=signal.action,
                reason=signal.reason,
            )
        return signal
