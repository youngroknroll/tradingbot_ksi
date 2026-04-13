from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import Position
from app.infra.db.models import PositionModel


class PositionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, symbol: str) -> Optional[Position]:
        stmt = select(PositionModel).where(PositionModel.symbol == symbol)
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        if row is None:
            return None
        return Position(
            symbol=row.symbol,
            quantity=row.quantity,
            average_price=row.average_price,
            realized_pnl=row.realized_pnl,
            unrealized_pnl=row.unrealized_pnl,
            updated_at=row.updated_at,
        )

    async def upsert(self, position: Position) -> None:
        stmt = select(PositionModel).where(PositionModel.symbol == position.symbol)
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()

        if row is None:
            row = PositionModel(
                symbol=position.symbol,
                quantity=position.quantity,
                average_price=position.average_price,
                realized_pnl=position.realized_pnl,
                unrealized_pnl=position.unrealized_pnl,
                updated_at=datetime.now(),
            )
            self._session.add(row)
        else:
            row.quantity = position.quantity
            row.average_price = position.average_price
            row.realized_pnl = position.realized_pnl
            row.unrealized_pnl = position.unrealized_pnl
            row.updated_at = datetime.now()

        await self._session.commit()

    async def get_all(self) -> List[Position]:
        stmt = select(PositionModel).where(PositionModel.quantity != 0)
        result = await self._session.execute(stmt)
        return [
            Position(
                symbol=r.symbol,
                quantity=r.quantity,
                average_price=r.average_price,
                realized_pnl=r.realized_pnl,
                unrealized_pnl=r.unrealized_pnl,
                updated_at=r.updated_at,
            )
            for r in result.scalars().all()
        ]

    async def get_total_realized_pnl(self) -> Decimal:
        positions = await self.get_all()
        return sum((p.realized_pnl for p in positions), Decimal("0"))
