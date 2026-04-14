import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.domain.enums import OrderSide, OrderStatus, OrderType, SignalAction


class Stock(BaseModel):
    symbol: str
    market: str = "KRX"
    name: str = ""


class Candle(BaseModel):
    symbol: str
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int


class Signal(BaseModel):
    symbol: str
    timestamp: datetime
    action: SignalAction
    reason: str = ""
    strength: float = Field(default=0.0, ge=0.0, le=1.0)


class Order(BaseModel):
    order_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    symbol: str
    side: OrderSide
    quantity: int
    price: Decimal = Decimal("0")
    order_type: OrderType = OrderType.MARKET
    status: OrderStatus = OrderStatus.PENDING
    idempotency_key: str = ""
    created_at: datetime = Field(default_factory=datetime.now)


class Fill(BaseModel):
    fill_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    order_id: str
    filled_quantity: int
    filled_price: Decimal
    filled_at: datetime = Field(default_factory=datetime.now)


class Position(BaseModel):
    symbol: str
    quantity: int = 0
    average_price: Decimal = Decimal("0")
    realized_pnl: Decimal = Decimal("0")
    unrealized_pnl: Decimal = Decimal("0")
    updated_at: datetime = Field(default_factory=datetime.now)


class Account(BaseModel):
    cash_balance: Decimal = Decimal("10000000")
    total_equity: Decimal = Decimal("10000000")
    available_buying_power: Decimal = Decimal("10000000")


class RiskRule(BaseModel):
    max_position_size: Decimal = Decimal("1000000")
    max_daily_loss: Decimal = Decimal("50000")
    max_symbol_exposure: Decimal = Decimal("500000")
    stop_loss_percent: Decimal = Decimal("3.0")
