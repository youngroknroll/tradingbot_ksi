from decimal import Decimal

from app.backtest.metrics import BacktestMetrics, calculate_metrics
from app.core.logging import get_logger
from app.domain.entities import Candle, Position
from app.domain.enums import SignalAction
from app.portfolio.calculator import (
    calculate_new_position_on_buy,
    calculate_new_position_on_sell,
)
from app.strategy.base import Strategy

logger = get_logger(__name__)


class BacktestEngine:
    def __init__(
        self,
        strategy: Strategy,
        initial_cash: float = 10_000_000,
        position_size_pct: float = 0.1,
    ) -> None:
        self._strategy = strategy
        self._initial_cash = initial_cash
        self._position_size_pct = position_size_pct

    def run(self, candles: list[Candle]) -> BacktestMetrics:
        cash = self._initial_cash
        position = Position(symbol=candles[0].symbol if candles else "")
        equity_curve: list[float] = []
        trade_pnls: list[float] = []
        min_candles = self._strategy.min_candles_required()

        for i in range(min_candles, len(candles)):
            window = candles[: i + 1]
            signal = self._strategy.compute_signal(window)
            current_price = float(candles[i].close)

            if signal and signal.action == SignalAction.BUY and position.quantity == 0:
                budget = cash * self._position_size_pct
                qty = int(budget / current_price)
                if qty > 0:
                    position = calculate_new_position_on_buy(
                        position, qty, Decimal(str(current_price))
                    )
                    cash -= qty * current_price

            elif signal and signal.action == SignalAction.SELL and position.quantity > 0:
                sell_value = position.quantity * current_price
                pnl = float(
                    (Decimal(str(current_price)) - position.average_price) * position.quantity
                )
                trade_pnls.append(pnl)
                position = calculate_new_position_on_sell(
                    position, position.quantity, Decimal(str(current_price))
                )
                cash += sell_value

            equity = cash + position.quantity * current_price
            equity_curve.append(equity)

        if not equity_curve:
            equity_curve = [self._initial_cash]

        metrics = calculate_metrics(equity_curve, trade_pnls)
        logger.info("backtest_complete", strategy=self._strategy.name, metrics=metrics.summary())
        return metrics
