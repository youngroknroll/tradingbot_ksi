import hashlib
from datetime import datetime
from decimal import Decimal

from app.domain.entities import Order, Signal
from app.domain.enums import OrderSide, OrderType


def create_order_from_signal(
    signal: Signal,
    quantity: int,
    price: Decimal,
    order_type: OrderType = OrderType.MARKET,
) -> Order:
    side = OrderSide.BUY if signal.action == "BUY" else OrderSide.SELL
    idempotency_key = _generate_idempotency_key(signal.symbol, side, signal.timestamp)

    return Order(
        symbol=signal.symbol,
        side=side,
        quantity=quantity,
        price=price,
        order_type=order_type,
        idempotency_key=idempotency_key,
    )


def _generate_idempotency_key(symbol: str, side: OrderSide, timestamp: datetime) -> str:
    raw = f"{symbol}:{side}:{timestamp.strftime('%Y%m%d%H%M')}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]
