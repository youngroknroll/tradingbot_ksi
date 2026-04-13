from typing import List, Optional

from app.domain.entities import Candle, Signal
from app.domain.enums import SignalAction
from app.strategy.base import Strategy


class MovingAverageCrossStrategy(Strategy):
    def __init__(self, short_window: int = 5, long_window: int = 20) -> None:
        self._short_window = short_window
        self._long_window = long_window

    @property
    def name(self) -> str:
        return f"MA_Cross_{self._short_window}_{self._long_window}"

    def min_candles_required(self) -> int:
        return self._long_window + 1

    def compute_signal(self, candles: List[Candle]) -> Optional[Signal]:
        if len(candles) < self.min_candles_required():
            return None

        closes = [float(c.close) for c in candles]

        prev_short = sum(closes[-(self._short_window + 1):-1]) / self._short_window
        prev_long = sum(closes[-(self._long_window + 1):-1]) / self._long_window

        curr_short = sum(closes[-self._short_window:]) / self._short_window
        curr_long = sum(closes[-self._long_window:]) / self._long_window

        symbol = candles[-1].symbol
        timestamp = candles[-1].timestamp

        if prev_short <= prev_long and curr_short > curr_long:
            return Signal(
                symbol=symbol,
                timestamp=timestamp,
                action=SignalAction.BUY,
                reason=f"Golden Cross: MA{self._short_window}({curr_short:.0f}) > MA{self._long_window}({curr_long:.0f})",
                strength=min((curr_short - curr_long) / curr_long * 100, 1.0),
            )

        if prev_short >= prev_long and curr_short < curr_long:
            return Signal(
                symbol=symbol,
                timestamp=timestamp,
                action=SignalAction.SELL,
                reason=f"Dead Cross: MA{self._short_window}({curr_short:.0f}) < MA{self._long_window}({curr_long:.0f})",
                strength=min((curr_long - curr_short) / curr_long * 100, 1.0),
            )

        return Signal(
            symbol=symbol,
            timestamp=timestamp,
            action=SignalAction.HOLD,
            reason="No crossover detected",
        )
