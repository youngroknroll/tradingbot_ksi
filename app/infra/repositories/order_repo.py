import uuid
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import Fill, Order
from app.domain.enums import OrderStatus
from app.infra.db.models import FillModel, OrderModel


class OrderRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, order: Order) -> Order:
        order_id = order.order_id or str(uuid.uuid4())
        model = OrderModel(
            order_id=order_id,
            symbol=order.symbol,
            side=order.side.value,
            quantity=order.quantity,
            price=order.price,
            order_type=order.order_type.value,
            status=order.status.value,
            idempotency_key=order.idempotency_key,
            created_at=order.created_at,
        )
        self._session.add(model)
        await self._session.commit()
        return Order(**{**order.model_dump(), "order_id": order_id})

    async def find_by_idempotency_key(self, key: str) -> Optional[Order]:
        stmt = select(OrderModel).where(OrderModel.idempotency_key == key)
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        if row is None:
            return None
        return Order(
            order_id=row.order_id,
            symbol=row.symbol,
            side=row.side,
            quantity=row.quantity,
            price=row.price,
            order_type=row.order_type,
            status=row.status,
            idempotency_key=row.idempotency_key,
            created_at=row.created_at,
        )

    async def update_status(self, order_id: str, status: OrderStatus) -> None:
        stmt = select(OrderModel).where(OrderModel.order_id == order_id)
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        if row:
            row.status = status.value
            await self._session.commit()

    async def update_status_atomic(
        self, order_id: str, status: OrderStatus, fill: Fill
    ) -> Order:
        stmt = select(OrderModel).where(OrderModel.order_id == order_id)
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        if row is None:
            raise ValueError(f"Order {order_id} not found")

        row.status = status.value

        fill_model = FillModel(
            fill_id=fill.fill_id,
            order_id=fill.order_id,
            filled_quantity=fill.filled_quantity,
            filled_price=fill.filled_price,
            filled_at=fill.filled_at,
        )
        self._session.add(fill_model)
        await self._session.commit()

        return Order(
            order_id=row.order_id,
            symbol=row.symbol,
            side=row.side,
            quantity=row.quantity,
            price=row.price,
            order_type=row.order_type,
            status=row.status,
            idempotency_key=row.idempotency_key,
            created_at=row.created_at,
        )

    async def get_open_orders(self, symbol: Optional[str] = None) -> List[Order]:
        stmt = select(OrderModel).where(
            OrderModel.status.in_([OrderStatus.PENDING.value, OrderStatus.SUBMITTED.value])
        )
        if symbol:
            stmt = stmt.where(OrderModel.symbol == symbol)
        result = await self._session.execute(stmt)
        return [
            Order(
                order_id=r.order_id,
                symbol=r.symbol,
                side=r.side,
                quantity=r.quantity,
                price=r.price,
                order_type=r.order_type,
                status=r.status,
                idempotency_key=r.idempotency_key,
                created_at=r.created_at,
            )
            for r in result.scalars().all()
        ]
