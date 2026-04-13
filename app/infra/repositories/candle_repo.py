from datetime import datetime
from typing import List

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import Candle
from app.infra.db.models import CandleModel


class CandleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert(self, candle: Candle) -> None:
        stmt = insert(CandleModel).values(
            symbol=candle.symbol,
            timestamp=candle.timestamp,
            open=candle.open,
            high=candle.high,
            low=candle.low,
            close=candle.close,
            volume=candle.volume,
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["symbol", "timestamp"],
            set_={
                "open": stmt.excluded.open,
                "high": stmt.excluded.high,
                "low": stmt.excluded.low,
                "close": stmt.excluded.close,
                "volume": stmt.excluded.volume,
            },
        )
        await self._session.execute(stmt)
        await self._session.commit()

    async def get_recent(self, symbol: str, limit: int = 100) -> List[Candle]:
        stmt = (
            select(CandleModel)
            .where(CandleModel.symbol == symbol)
            .order_by(CandleModel.timestamp.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        rows = result.scalars().all()
        return [
            Candle(
                symbol=r.symbol,
                timestamp=r.timestamp,
                open=r.open,
                high=r.high,
                low=r.low,
                close=r.close,
                volume=r.volume,
            )
            for r in reversed(rows)
        ]

    async def get_range(
        self, symbol: str, start: datetime, end: datetime
    ) -> List[Candle]:
        stmt = (
            select(CandleModel)
            .where(
                CandleModel.symbol == symbol,
                CandleModel.timestamp >= start,
                CandleModel.timestamp <= end,
            )
            .order_by(CandleModel.timestamp.asc())
        )
        result = await self._session.execute(stmt)
        rows = result.scalars().all()
        return [
            Candle(
                symbol=r.symbol,
                timestamp=r.timestamp,
                open=r.open,
                high=r.high,
                low=r.low,
                close=r.close,
                volume=r.volume,
            )
            for r in rows
        ]
