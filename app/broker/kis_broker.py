import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional

import httpx

from app.broker.base import Broker
from app.core.config import settings
from app.core.exceptions import BrokerConnectionError, BrokerError
from app.core.logging import get_logger
from app.domain.entities import Account, Fill, Order
from app.domain.enums import OrderSide

logger = get_logger(__name__)

_TOKEN_REFRESH_MARGIN_HOURS = 1


class KISBroker(Broker):
    def __init__(self) -> None:
        self._access_token: str = ""
        self._token_expires_at: Optional[datetime] = None
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=10.0)
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def _get_token(self) -> str:
        if (
            self._access_token
            and self._token_expires_at
            and datetime.now() < self._token_expires_at
        ):
            return self._access_token

        url = f"{settings.kis_base_url}/oauth2/tokenP"
        body = {
            "grant_type": "client_credentials",
            "appkey": settings.kis_app_key,
            "appsecret": settings.kis_app_secret,
        }
        client = await self._get_client()
        try:
            resp = await client.post(url, json=body)
            resp.raise_for_status()
            data = resp.json()
            self._access_token = data["access_token"]
            expires_in = int(data.get("expires_in", 86400))
            self._token_expires_at = datetime.now() + timedelta(
                seconds=expires_in
            ) - timedelta(hours=_TOKEN_REFRESH_MARGIN_HOURS)
            return self._access_token
        except httpx.HTTPError as e:
            self._access_token = ""
            self._token_expires_at = None
            raise BrokerConnectionError(f"KIS token error: {e}") from e

    async def submit_order(self, order: Order) -> Optional[Fill]:
        token = await self._get_token()

        tr_id = "VTTC0802U" if settings.kis_is_paper else "TTTC0802U"
        if order.side == OrderSide.SELL:
            tr_id = "VTTC0801U" if settings.kis_is_paper else "TTTC0801U"

        url = f"{settings.kis_base_url}/uapi/domestic-stock/v1/trading/order-cash"
        headers = {
            "authorization": f"Bearer {token}",
            "appkey": settings.kis_app_key,
            "appsecret": settings.kis_app_secret,
            "tr_id": tr_id,
        }
        body = {
            "CANO": settings.kis_account_number[:8],
            "ACNT_PRDT_CD": settings.kis_account_number[8:],
            "PDNO": order.symbol,
            "ORD_DVSN": "01",
            "ORD_QTY": str(order.quantity),
            "ORD_UNPR": str(int(order.price)),
        }

        client = await self._get_client()
        try:
            resp = await client.post(url, headers=headers, json=body)
            resp.raise_for_status()
            data = resp.json()
        except httpx.HTTPError as e:
            raise BrokerError(f"KIS order failed: {e}") from e

        if data.get("rt_cd") != "0":
            raise BrokerError(f"KIS order rejected: {data.get('msg1', 'unknown')}")

        output = data.get("output", {})
        filled_qty = int(output.get("ORD_QTY", order.quantity))
        filled_price = Decimal(output.get("ORD_UNPR", str(order.price)))

        logger.info("kis_order_submitted", order_id=order.order_id, response=data.get("msg1"))
        return Fill(
            fill_id=str(uuid.uuid4()),
            order_id=order.order_id,
            filled_quantity=filled_qty,
            filled_price=filled_price,
            filled_at=datetime.now(),
        )

    async def get_account(self) -> Account:
        token = await self._get_token()
        tr_id = "VTTC8434R" if settings.kis_is_paper else "TTTC8434R"

        url = f"{settings.kis_base_url}/uapi/domestic-stock/v1/trading/inquire-balance"
        headers = {
            "authorization": f"Bearer {token}",
            "appkey": settings.kis_app_key,
            "appsecret": settings.kis_app_secret,
            "tr_id": tr_id,
        }
        params = {
            "CANO": settings.kis_account_number[:8],
            "ACNT_PRDT_CD": settings.kis_account_number[8:],
            "AFHR_FLPR_YN": "N",
            "OFL_YN": "",
            "INQR_DVSN": "02",
            "UNPR_DVSN": "01",
            "FUND_STTL_ICLD_YN": "N",
            "FNCG_AMT_AUTO_RDPT_YN": "N",
            "PRCS_DVSN": "01",
            "CTX_AREA_FK100": "",
            "CTX_AREA_NK100": "",
        }

        client = await self._get_client()
        try:
            resp = await client.get(url, headers=headers, params=params)
            resp.raise_for_status()
            data = resp.json()
        except httpx.HTTPError as e:
            raise BrokerConnectionError(f"KIS account query failed: {e}") from e

        output2 = data.get("output2", [{}])
        if output2:
            info = output2[0]
            return Account(
                cash_balance=Decimal(info.get("dnca_tot_amt", "0")),
                total_equity=Decimal(info.get("tot_evlu_amt", "0")),
                available_buying_power=Decimal(info.get("nass_amt", "0")),
            )
        return Account()

    async def cancel_order(self, order_id: str) -> bool:
        token = await self._get_token()

        url = f"{settings.kis_base_url}/uapi/domestic-stock/v1/trading/order-rvsecncl"
        tr_id = "VTTC0803U" if settings.kis_is_paper else "TTTC0803U"
        headers = {
            "authorization": f"Bearer {token}",
            "appkey": settings.kis_app_key,
            "appsecret": settings.kis_app_secret,
            "tr_id": tr_id,
        }
        body = {
            "CANO": settings.kis_account_number[:8],
            "ACNT_PRDT_CD": settings.kis_account_number[8:],
            "KRX_FWDG_ORD_ORGNO": "",
            "ORGN_ODNO": order_id,
            "ORD_DVSN": "01",
            "RVSE_CNCL_DVSN_CD": "02",
            "ORD_QTY": "0",
            "ORD_UNPR": "0",
            "QTY_ALL_ORD_YN": "Y",
        }

        client = await self._get_client()
        try:
            resp = await client.post(url, headers=headers, json=body)
            resp.raise_for_status()
            data = resp.json()
        except httpx.HTTPError as e:
            logger.error("kis_cancel_failed", order_id=order_id, error=str(e))
            return False

        if data.get("rt_cd") != "0":
            logger.error("kis_cancel_rejected", order_id=order_id, msg=data.get("msg1"))
            return False

        logger.info("kis_order_cancelled", order_id=order_id)
        return True
