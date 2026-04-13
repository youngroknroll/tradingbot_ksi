from dataclasses import dataclass
from decimal import Decimal

from app.domain.entities import Account, Position, RiskRule


@dataclass(frozen=True)
class RiskCheckResult:
    passed: bool
    reason: str = ""


def check_position_size(
    order_value: Decimal, rule: RiskRule
) -> RiskCheckResult:
    if order_value > rule.max_position_size:
        return RiskCheckResult(
            passed=False,
            reason=f"Order value {order_value} exceeds max position size {rule.max_position_size}",
        )
    return RiskCheckResult(passed=True)


def check_daily_loss(
    current_daily_loss: Decimal, rule: RiskRule
) -> RiskCheckResult:
    if abs(current_daily_loss) >= rule.max_daily_loss:
        return RiskCheckResult(
            passed=False,
            reason=f"Daily loss {current_daily_loss} exceeds max {rule.max_daily_loss}",
        )
    return RiskCheckResult(passed=True)


def check_buying_power(
    order_value: Decimal, account: Account
) -> RiskCheckResult:
    if order_value > account.available_buying_power:
        return RiskCheckResult(
            passed=False,
            reason=f"Order value {order_value} exceeds buying power {account.available_buying_power}",
        )
    return RiskCheckResult(passed=True)


def check_stop_loss(
    position: Position, current_price: Decimal, rule: RiskRule
) -> RiskCheckResult:
    if position.quantity <= 0:
        return RiskCheckResult(passed=True)

    loss_percent = float(
        (position.average_price - current_price) / position.average_price * 100
    )
    if loss_percent >= rule.stop_loss_percent:
        return RiskCheckResult(
            passed=False,
            reason=f"Stop loss triggered: {loss_percent:.1f}% loss exceeds {rule.stop_loss_percent}%",
        )
    return RiskCheckResult(passed=True)
