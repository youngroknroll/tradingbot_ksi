from decimal import Decimal
from typing import List

from app.core.logging import get_logger
from app.domain.entities import Fill, Order, Position
from app.domain.enums import OrderSide
from app.infra.repositories.position_repo import PositionRepository
from app.portfolio.calculator import (
    calculate_new_position_on_buy,
    calculate_new_position_on_sell,
    calculate_unrealized_pnl,
)

logger = get_logger(__name__)


class PortfolioService:
    def __init__(self, position_repo: PositionRepository) -> None:
        self._position_repo = position_repo

    async def update_on_fill(self, order: Order, fill: Fill) -> Position:
        current = await self._position_repo.get(order.symbol)
        if current is None:
            current = Position(symbol=order.symbol)

        if order.side == OrderSide.BUY:
            new_position = calculate_new_position_on_buy(
                current, fill.filled_quantity, fill.filled_price
            )
        else:
            new_position = calculate_new_position_on_sell(
                current, fill.filled_quantity, fill.filled_price
            )

        await self._position_repo.upsert(new_position)
        logger.info(
            "position_updated",
            symbol=order.symbol,
            quantity=new_position.quantity,
            avg_price=str(new_position.average_price),
            realized_pnl=str(new_position.realized_pnl),
        )
        return new_position

    async def get_position(self, symbol: str) -> Position:
        pos = await self._position_repo.get(symbol)
        return pos or Position(symbol=symbol)

    async def get_all_positions(self) -> List[Position]:
        return await self._position_repo.get_all()

    async def update_unrealized_pnl(
        self, symbol: str, current_price: Decimal
    ) -> Position:
        position = await self.get_position(symbol)
        unrealized = calculate_unrealized_pnl(position, current_price)
        updated = Position(
            **{**position.model_dump(), "unrealized_pnl": unrealized}
        )
        await self._position_repo.upsert(updated)
        return updated
