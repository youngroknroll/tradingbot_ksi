import uuid
from datetime import datetime
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


class KISBroker(Broker):
    def __init__(self) -> None:
        self._access_token: str = ""

    async def _get_token(self) -> str:
        if self._access_token:
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
                self._access_token = resp.json()["access_token"]
                return self._access_token
            except httpx.HTTPError as e:
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

        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(url, headers=headers, json=body, timeout=10.0)
                resp.raise_for_status()
                data = resp.json()
            except httpx.HTTPError as e:
                raise BrokerError(f"KIS order failed: {e}") from e

        if data.get("rt_cd") != "0":
            raise BrokerError(f"KIS order rejected: {data.get('msg1', 'unknown')}")

        logger.info("kis_order_submitted", order_id=order.order_id, response=data.get("msg1"))
        return Fill(
            fill_id=str(uuid.uuid4()),
            order_id=order.order_id,
            filled_quantity=order.quantity,
            filled_price=order.price,
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

        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(url, headers=headers, params=params, timeout=10.0)
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
        logger.warning("kis_cancel_not_implemented", order_id=order_id)
        return False
