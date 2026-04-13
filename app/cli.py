import argparse
import asyncio
import sys
from datetime import datetime
from decimal import Decimal

from app.backtest.engine import BacktestEngine
from app.core.logging import setup_logging, get_logger
from app.domain.entities import Candle
from app.strategy.moving_average import MovingAverageCrossStrategy

logger = get_logger(__name__)


def generate_sample_candles(symbol: str, days: int = 100) -> list[Candle]:
    """Generate sample candle data for backtest demo."""
    import random

    random.seed(42)
    candles = []
    price = 50000.0

    for i in range(days):
        change = random.gauss(0, 0.02)
        price *= 1 + change
        high = price * (1 + abs(random.gauss(0, 0.01)))
        low = price * (1 - abs(random.gauss(0, 0.01)))
        candles.append(
            Candle(
                symbol=symbol,
                timestamp=datetime(2026, 1, 1) + __import__("datetime").timedelta(days=i),
                open=Decimal(str(round(price * (1 + random.gauss(0, 0.005)), 0))),
                high=Decimal(str(round(high, 0))),
                low=Decimal(str(round(low, 0))),
                close=Decimal(str(round(price, 0))),
                volume=random.randint(100000, 1000000),
            )
        )
    return candles


def run_backtest(symbol: str, short: int, long: int) -> None:
    setup_logging()
    strategy = MovingAverageCrossStrategy(short_window=short, long_window=long)
    engine = BacktestEngine(strategy, initial_cash=10_000_000, position_size_pct=0.1)

    print(f"\nRunning backtest: {strategy.name} on {symbol}")
    print("-" * 40)

    candles = generate_sample_candles(symbol, days=200)
    metrics = engine.run(candles)
    print(metrics.summary())


def main() -> None:
    parser = argparse.ArgumentParser(description="Trading Bot CLI")
    subparsers = parser.add_subparsers(dest="command")

    bt_parser = subparsers.add_parser("backtest", help="Run backtest")
    bt_parser.add_argument("--symbol", default="005930", help="Stock symbol (default: 삼성전자)")
    bt_parser.add_argument("--short", type=int, default=5, help="Short MA window")
    bt_parser.add_argument("--long", type=int, default=20, help="Long MA window")

    server_parser = subparsers.add_parser("server", help="Start API server")
    server_parser.add_argument("--port", type=int, default=8000)

    args = parser.parse_args()

    if args.command == "backtest":
        run_backtest(args.symbol, args.short, args.long)
    elif args.command == "server":
        import uvicorn
        uvicorn.run("main:app", host="0.0.0.0", port=args.port, reload=True)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
