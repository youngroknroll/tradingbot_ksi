from decimal import Decimal

from app.domain.entities import Account, Position, RiskRule
from app.risk.rules import (
    check_buying_power,
    check_daily_loss,
    check_position_size,
    check_stop_loss,
)


class TestRiskRules:
    def setup_method(self):
        self.rule = RiskRule(
            max_position_size=Decimal("1000000"),
            max_daily_loss=Decimal("50000"),
            stop_loss_percent=Decimal("3.0"),
        )

    def test_position_size_within_limit(self):
        result = check_position_size(Decimal("500000"), self.rule)
        assert result.passed is True

    def test_position_size_exceeds_limit(self):
        result = check_position_size(Decimal("1500000"), self.rule)
        assert result.passed is False
        assert "max position size" in result.reason

    def test_daily_loss_within_limit(self):
        result = check_daily_loss(Decimal("-30000"), self.rule)
        assert result.passed is True

    def test_daily_loss_exceeds_limit(self):
        result = check_daily_loss(Decimal("-60000"), self.rule)
        assert result.passed is False

    def test_buying_power_sufficient(self):
        account = Account(available_buying_power=Decimal("5000000"))
        result = check_buying_power(Decimal("1000000"), account)
        assert result.passed is True

    def test_buying_power_insufficient(self):
        account = Account(available_buying_power=Decimal("500000"))
        result = check_buying_power(Decimal("1000000"), account)
        assert result.passed is False

    def test_stop_loss_not_triggered(self):
        position = Position(
            symbol="005930", quantity=10, average_price=Decimal("50000")
        )
        result = check_stop_loss(position, Decimal("49000"), self.rule)
        assert result.passed is True

    def test_stop_loss_triggered(self):
        position = Position(
            symbol="005930", quantity=10, average_price=Decimal("50000")
        )
        result = check_stop_loss(position, Decimal("48000"), self.rule)
        assert result.passed is False

    def test_stop_loss_no_position(self):
        position = Position(symbol="005930", quantity=0)
        result = check_stop_loss(position, Decimal("48000"), self.rule)
        assert result.passed is True
