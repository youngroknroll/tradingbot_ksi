from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import verify_api_key
from app.infra.db.connection import get_session
from app.infra.repositories.position_repo import PositionRepository
from app.monitoring.healthcheck import HealthCheckService

router = APIRouter(dependencies=[Depends(verify_api_key)])


@router.get("/health")
async def health(session: AsyncSession = Depends(get_session)):
    service = HealthCheckService(session)
    return await service.check()


@router.get("/positions")
async def list_positions(session: AsyncSession = Depends(get_session)):
    repo = PositionRepository(session)
    positions = await repo.get_all()
    return [p.model_dump() for p in positions]


@router.get("/positions/{symbol}")
async def get_position(symbol: str, session: AsyncSession = Depends(get_session)):
    repo = PositionRepository(session)
    pos = await repo.get(symbol)
    if pos is None:
        return {"symbol": symbol, "quantity": 0}
    return pos.model_dump()
