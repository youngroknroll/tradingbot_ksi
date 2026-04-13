import uuid
from datetime import datetime
from decimal import Decimal

from app.broker.base import Broker
from app.core.logging import get_logger
from app.domain.entities import Account, Fill, Order
from app.domain.enums import OrderSide

logger = get_logger(__name__)


class FakeBroker(Broker):
    def __init__(self, initial_cash: Decimal = Decimal("10000000")) -> None:
        self._cash = initial_cash
        self._initial_cash = initial_cash

    async def submit_order(self, order: Order) -> Fill:
        fill_price = order.price
        fill_value = fill_price * order.quantity

        if order.side == OrderSide.BUY:
            self._cash -= fill_value
        else:
            self._cash += fill_value

        fill = Fill(
            fill_id=str(uuid.uuid4()),
            order_id=order.order_id,
            filled_quantity=order.quantity,
            filled_price=fill_price,
            filled_at=datetime.now(),
        )

        logger.info(
            "fake_fill",
            order_id=order.order_id,
            side=order.side,
            price=str(fill_price),
            quantity=order.quantity,
            cash_remaining=str(self._cash),
        )
        return fill

    async def get_account(self) -> Account:
        return Account(
            cash_balance=self._cash,
            total_equity=self._cash,
            available_buying_power=self._cash,
        )

    async def cancel_order(self, order_id: str) -> bool:
        logger.info("fake_cancel", order_id=order_id)
        return True
