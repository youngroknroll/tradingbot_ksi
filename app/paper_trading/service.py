import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional

from app.broker.fake_broker import FakeBroker
from app.core.exceptions import DuplicateOrderError, RiskLimitExceededError
from app.core.logging import get_logger
from app.domain.entities import RiskRule
from app.domain.enums import SignalAction
from app.execution.order_factory import create_order_from_signal
from app.execution.service import ExecutionService
from app.infra.repositories.order_repo import OrderRepository
from app.infra.repositories.position_repo import PositionRepository
from app.market_data.service import MarketDataService
from app.portfolio.service import PortfolioService
from app.risk.service import RiskService
from app.strategy.base import Strategy
from app.strategy.service import StrategyService

logger = get_logger(__name__)

_LOOKBACK_DAYS = 60


class PaperTradingService:
    def __init__(
        self,
        strategy: Strategy,
        symbols: List[str],
        market_data: MarketDataService,
        order_repo: OrderRepository,
        position_repo: PositionRepository,
        risk_rule: Optional[RiskRule] = None,
    ) -> None:
        self._strategy_service = StrategyService(strategy)
        self._symbols = symbols
        self._market_data = market_data
        self._broker = FakeBroker()
        self._execution = ExecutionService(self._broker, order_repo)
        self._portfolio = PortfolioService(position_repo)
        self._risk = RiskService(risk_rule or RiskRule())
        self._running = False

    async def run_cycle(self) -> None:
        today = datetime.now()
        start_date = (today - timedelta(days=_LOOKBACK_DAYS)).strftime("%Y%m%d")
        end_date = today.strftime("%Y%m%d")

        for symbol in self._symbols:
            try:
                candles = await self._market_data.fetch_daily_candles(
                    symbol,
                    start_date=start_date,
                    end_date=end_date,
                )
                signal = self._strategy_service.evaluate(candles)
                if signal is None or signal.action == SignalAction.HOLD:
                    continue

                current_price = candles[-1].close
                position = await self._portfolio.get_position(symbol)
                account = await self._broker.get_account()

                if signal.action == SignalAction.BUY and position.quantity == 0:
                    budget = account.available_buying_power * Decimal("0.1")
                    qty = int(budget / current_price)
                    if qty <= 0:
                        continue
                    order = create_order_from_signal(signal, qty, current_price)
                    self._risk.validate_order(order, account)
                    order_result, fill = await self._execution.submit_order(order)
                    if fill:
                        await self._portfolio.update_on_fill(order_result, fill)

                elif signal.action == SignalAction.SELL and position.quantity > 0:
                    order = create_order_from_signal(
                        signal, position.quantity, current_price
                    )
                    self._risk.validate_order(order, account)
                    order_result, fill = await self._execution.submit_order(order)
                    if fill:
                        await self._portfolio.update_on_fill(order_result, fill)

            except DuplicateOrderError:
                logger.debug("duplicate_order_skipped", symbol=symbol)
            except RiskLimitExceededError as e:
                logger.warning("risk_blocked", symbol=symbol, reason=str(e))
            except Exception as e:
                logger.error("paper_trading_error", symbol=symbol, error=str(e))

    async def run_loop(self, interval_seconds: int = 60) -> None:
        self._running = True
        logger.info("paper_trading_started", symbols=self._symbols)
        while self._running:
            await self.run_cycle()
            await asyncio.sleep(interval_seconds)

    def stop(self) -> None:
        self._running = False
        logger.info("paper_trading_stopped")
