from datetime import datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger

logger = get_logger(__name__)


class HealthCheckService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def check(self) -> dict:
        db_ok = await self._check_db()
        return {
            "status": "healthy" if db_ok else "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "checks": {
                "database": "ok" if db_ok else "error",
            },
        }

    async def _check_db(self) -> bool:
        try:
            await self._session.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error("db_health_check_failed", error=str(e))
            return False
