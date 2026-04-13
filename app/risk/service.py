from decimal import Decimal

from app.core.exceptions import RiskLimitExceededError
from app.core.logging import get_logger
from app.domain.entities import Account, Order, Position, RiskRule
from app.domain.enums import OrderSide
from app.risk.rules import (
    check_buying_power,
    check_daily_loss,
    check_position_size,
    check_stop_loss,
)

logger = get_logger(__name__)


class RiskService:
    def __init__(self, rule: RiskRule) -> None:
        self._rule = rule

    def validate_order(
        self,
        order: Order,
        account: Account,
        current_daily_loss: Decimal = Decimal("0"),
    ) -> None:
        order_value = order.price * order.quantity

        checks = [
            check_position_size(order_value, self._rule),
            check_daily_loss(current_daily_loss, self._rule),
        ]

        if order.side == OrderSide.BUY:
            checks.append(check_buying_power(order_value, account))

        for result in checks:
            if not result.passed:
                logger.warning("risk_check_failed", reason=result.reason, order_id=order.order_id)
                raise RiskLimitExceededError(result.reason)

        logger.info("risk_check_passed", order_id=order.order_id, value=str(order_value))

    def should_stop_loss(self, position: Position, current_price: Decimal) -> bool:
        result = check_stop_loss(position, current_price, self._rule)
        if not result.passed:
            logger.warning("stop_loss_triggered", symbol=position.symbol, reason=result.reason)
        return not result.passed
