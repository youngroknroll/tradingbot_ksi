from abc import ABC, abstractmethod
from typing import Optional

from app.domain.entities import Account, Fill, Order


class Broker(ABC):
    @abstractmethod
    async def submit_order(self, order: Order) -> Optional[Fill]:
        ...

    @abstractmethod
    async def get_account(self) -> Account:
        ...

    @abstractmethod
    async def cancel_order(self, order_id: str) -> bool:
        ...
