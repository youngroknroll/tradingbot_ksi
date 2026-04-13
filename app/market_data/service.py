from datetime import datetime
from decimal import Decimal
from typing import List, Optional

import httpx

from app.core.config import settings
from app.core.exceptions import MarketDataError
from app.core.logging import get_logger
from app.domain.entities import Candle

logger = get_logger(__name__)


class MarketDataService:
    def __init__(self) -> None:
        self._access_token: str = ""
        self._token_expires: Optional[datetime] = None

    async def _get_access_token(self) -> str:
        if self._access_token and self._token_expires and datetime.now() < self._token_expires:
            return self._access_token

        url = f"{settings.kis_base_url}/oauth2/tokenP"
        body = {
            "grant_type": "client_credentials",
            "appkey": settings.kis_app_key,
            "appsecret": settings.kis_app_secret,
        }
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(url, json=body, timeout=10.0)
                resp.raise_for_status()
                data = resp.json()
                self._access_token = data["access_token"]
                self._token_expires = datetime.now()
                return self._access_token
            except httpx.HTTPError as e:
                raise MarketDataError(f"Failed to get access token: {e}") from e

    async def fetch_daily_candles(
        self, symbol: str, start_date: str, end_date: str
    ) -> List[Candle]:
        token = await self._get_access_token()

        url = f"{settings.kis_base_url}/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice"
        headers = {
            "authorization": f"Bearer {token}",
            "appkey": settings.kis_app_key,
            "appsecret": settings.kis_app_secret,
            "tr_id": "FHKST03010100",
        }
        params = {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD": symbol,
            "FID_INPUT_DATE_1": start_date,
            "FID_INPUT_DATE_2": end_date,
            "FID_PERIOD_DIV_CODE": "D",
            "FID_ORG_ADJ_PRC": "0",
        }

        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(url, headers=headers, params=params, timeout=10.0)
                resp.raise_for_status()
                data = resp.json()
            except httpx.HTTPError as e:
                raise MarketDataError(f"Failed to fetch candles for {symbol}: {e}") from e

        candles: List[Candle] = []
        for item in data.get("output2", []):
            try:
                candles.append(
                    Candle(
                        symbol=symbol,
                        timestamp=datetime.strptime(item["stck_bsop_date"], "%Y%m%d"),
                        open=Decimal(item["stck_oprc"]),
                        high=Decimal(item["stck_hgpr"]),
                        low=Decimal(item["stck_lwpr"]),
                        close=Decimal(item["stck_clpr"]),
                        volume=int(item["acml_vol"]),
                    )
                )
            except (KeyError, ValueError) as e:
                logger.warning("skipping_candle", symbol=symbol, error=str(e))

        return sorted(candles, key=lambda c: c.timestamp)

    async def fetch_current_price(self, symbol: str) -> Decimal:
        token = await self._get_access_token()

        url = f"{settings.kis_base_url}/uapi/domestic-stock/v1/quotations/inquire-price"
        headers = {
            "authorization": f"Bearer {token}",
            "appkey": settings.kis_app_key,
            "appsecret": settings.kis_app_secret,
            "tr_id": "FHKST01010100",
        }
        params = {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD": symbol,
        }

        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(url, headers=headers, params=params, timeout=10.0)
                resp.raise_for_status()
                data = resp.json()
                return Decimal(data["output"]["stck_prpr"])
            except (httpx.HTTPError, KeyError) as e:
                raise MarketDataError(f"Failed to fetch price for {symbol}: {e}") from e
