from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Index, Integer, Numeric, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class CandleModel(Base):
    __tablename__ = "candles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    open: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    high: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    low: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    close: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    volume: Mapped[int] = mapped_column(Integer, nullable=False)

    __table_args__ = (
        Index("ix_candles_symbol_timestamp", "symbol", "timestamp", unique=True),
    )


class OrderModel(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    side: Mapped[str] = mapped_column(String(10), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=0)
    order_type: Mapped[str] = mapped_column(String(10), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDING")
    idempotency_key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())


class FillModel(Base):
    __tablename__ = "fills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    fill_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    order_id: Mapped[str] = mapped_column(String(50), nullable=False)
    filled_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    filled_price: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    filled_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())


class PositionModel(Base):
    __tablename__ = "positions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    average_price: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=0)
    realized_pnl: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=0)
    unrealized_pnl: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())
