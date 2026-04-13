from app.execution.order_factory import _generate_idempotency_key, create_order_from_signal
from datetime import datetime
from decimal import Decimal

from app.domain.entities import Signal
from app.domain.enums import OrderSide, SignalAction


class TestOrderFactory:
    def test_create_buy_order_from_signal(self):
        signal = Signal(
            symbol="005930",
            timestamp=datetime(2026, 4, 13),
            action=SignalAction.BUY,
            reason="test",
        )
        order = create_order_from_signal(signal, quantity=10, price=Decimal("50000"))
        assert order.side == OrderSide.BUY
        assert order.quantity == 10
        assert order.price == Decimal("50000")
        assert order.idempotency_key != ""

    def test_create_sell_order_from_signal(self):
        signal = Signal(
            symbol="005930",
            timestamp=datetime(2026, 4, 13),
            action=SignalAction.SELL,
            reason="test",
        )
        order = create_order_from_signal(signal, quantity=5, price=Decimal("55000"))
        assert order.side == OrderSide.SELL
        assert order.quantity == 5

    def test_idempotency_key_deterministic(self):
        ts = datetime(2026, 4, 13, 10, 30)
        key1 = _generate_idempotency_key("005930", OrderSide.BUY, ts)
        key2 = _generate_idempotency_key("005930", OrderSide.BUY, ts)
        assert key1 == key2

    def test_idempotency_key_differs_by_symbol(self):
        ts = datetime(2026, 4, 13, 10, 30)
        key1 = _generate_idempotency_key("005930", OrderSide.BUY, ts)
        key2 = _generate_idempotency_key("035720", OrderSide.BUY, ts)
        assert key1 != key2

    def test_idempotency_key_differs_by_side(self):
        ts = datetime(2026, 4, 13, 10, 30)
        key1 = _generate_idempotency_key("005930", OrderSide.BUY, ts)
        key2 = _generate_idempotency_key("005930", OrderSide.SELL, ts)
        assert key1 != key2
