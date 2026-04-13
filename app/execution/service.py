from typing import Optional, Tuple

from app.broker.base import Broker
from app.core.exceptions import DuplicateOrderError
from app.core.logging import get_logger
from app.domain.entities import Fill, Order
from app.domain.enums import OrderStatus
from app.infra.repositories.order_repo import OrderRepository

logger = get_logger(__name__)


class ExecutionService:
    def __init__(self, broker: Broker, order_repo: OrderRepository) -> None:
        self._broker = broker
        self._order_repo = order_repo

    async def submit_order(self, order: Order) -> Tuple[Order, Optional[Fill]]:
        existing = await self._order_repo.find_by_idempotency_key(order.idempotency_key)
        if existing:
            logger.info("duplicate_order_skipped", idempotency_key=order.idempotency_key)
            raise DuplicateOrderError(
                f"Order with idempotency key {order.idempotency_key} already exists"
            )

        saved_order = await self._order_repo.save(order)
        logger.info(
            "order_created",
            order_id=saved_order.order_id,
            symbol=saved_order.symbol,
            side=saved_order.side,
            quantity=saved_order.quantity,
        )

        try:
            fill = await self._broker.submit_order(saved_order)
            if fill:
                await self._order_repo.update_status(saved_order.order_id, OrderStatus.FILLED)
                saved_order = Order(**{**saved_order.model_dump(), "status": OrderStatus.FILLED})
                logger.info(
                    "order_filled",
                    order_id=saved_order.order_id,
                    filled_price=str(fill.filled_price),
                    filled_quantity=fill.filled_quantity,
                )
            else:
                await self._order_repo.update_status(saved_order.order_id, OrderStatus.SUBMITTED)
                saved_order = Order(
                    **{**saved_order.model_dump(), "status": OrderStatus.SUBMITTED}
                )
        except Exception as e:
            await self._order_repo.update_status(saved_order.order_id, OrderStatus.REJECTED)
            logger.error("order_rejected", order_id=saved_order.order_id, error=str(e))
            raise

        return saved_order, fill
