from datetime import datetime, timedelta
from decimal import Decimal

from app.domain.entities import Candle
from app.domain.enums import SignalAction
from app.strategy.moving_average import MovingAverageCrossStrategy


def _make_candle(day: int, close: float) -> Candle:
    return Candle(
        symbol="005930",
        timestamp=datetime(2026, 1, 1) + timedelta(days=day),
        open=Decimal(str(close)),
        high=Decimal(str(close + 100)),
        low=Decimal(str(close - 100)),
        close=Decimal(str(close)),
        volume=100000,
    )


class TestMovingAverageCrossStrategy:
    def test_insufficient_candles_returns_none(self):
        strategy = MovingAverageCrossStrategy(short_window=5, long_window=20)
        candles = [_make_candle(i, 50000) for i in range(10)]
        assert strategy.compute_signal(candles) is None

    def test_golden_cross_buy_signal(self):
        strategy = MovingAverageCrossStrategy(short_window=3, long_window=5)
        # prev: short MA(85,80,82)=82.3 < long MA(95,90,85,80,82)=86.4
        # curr: short MA(80,82,88)=83.3 ... need short > long
        # Use data where crossover clearly happens at last candle
        prices = [100, 95, 90, 85, 80, 78, 76, 80, 90, 100]
        candles = [_make_candle(i, p) for i, p in enumerate(prices)]
        signal = strategy.compute_signal(candles)
        assert signal is not None
        # Verify it's either BUY or computes correctly
        # Let's compute: prev_short=avg(76,80,90)=82, prev_long=avg(80,78,76,80,90)=80.8
        # curr_short=avg(80,90,100)=90, curr_long=avg(78,76,80,90,100)=84.8
        # prev_short(82) > prev_long(80.8), curr_short(90) > curr_long(84.8) -> no cross, HOLD
        # Need: prev_short <= prev_long AND curr_short > curr_long
        # Try different data
        prices2 = [100, 98, 96, 94, 92, 90, 88, 92, 98, 106]
        candles2 = [_make_candle(i, p) for i, p in enumerate(prices2)]
        signal2 = strategy.compute_signal(candles2)
        # prev_short=avg(88,92,98)=92.67, prev_long=avg(92,90,88,92,98)=92.0
        # curr_short=avg(92,98,106)=98.67, curr_long=avg(90,88,92,98,106)=94.8
        # prev_short(92.67) > prev_long(92.0) -> no cross
        # Need sustained decline then sharp rise
        prices3 = [100, 95, 90, 85, 80, 75, 70, 68, 80, 95]
        candles3 = [_make_candle(i, p) for i, p in enumerate(prices3)]
        signal3 = strategy.compute_signal(candles3)
        # prev_short=avg(68,80)... let me just compute
        # prev window = candles[5:9] -> prev_short=avg(70,68,80)=72.67, prev_long=avg(80,75,70,68,80)=74.6
        # curr window = candles[6:10] -> curr_short=avg(68,80,95)=81, curr_long=avg(75,70,68,80,95)=77.6
        # prev_short(72.67) < prev_long(74.6) AND curr_short(81) > curr_long(77.6) -> GOLDEN CROSS!
        assert signal3 is not None
        assert signal3.action == SignalAction.BUY

    def test_dead_cross_sell_signal(self):
        strategy = MovingAverageCrossStrategy(short_window=3, long_window=5)
        # Need: prev_short >= prev_long AND curr_short < curr_long
        # Rising then sharp drop
        prices = [70, 75, 80, 85, 90, 95, 100, 102, 90, 75]
        candles = [_make_candle(i, p) for i, p in enumerate(prices)]
        signal = strategy.compute_signal(candles)
        # prev_short=avg(100,102,90)=97.33, prev_long=avg(90,95,100,102,90)=95.4
        # curr_short=avg(102,90,75)=89, curr_long=avg(95,100,102,90,75)=92.4
        # prev_short(97.33) > prev_long(95.4) AND curr_short(89) < curr_long(92.4) -> DEAD CROSS!
        assert signal is not None
        assert signal.action == SignalAction.SELL

    def test_flat_prices_hold(self):
        strategy = MovingAverageCrossStrategy(short_window=3, long_window=5)
        candles = [_make_candle(i, 50000) for i in range(10)]
        signal = strategy.compute_signal(candles)
        assert signal is not None
        assert signal.action == SignalAction.HOLD

    def test_min_candles_required(self):
        strategy = MovingAverageCrossStrategy(short_window=5, long_window=20)
        assert strategy.min_candles_required() == 21

    def test_strategy_name(self):
        strategy = MovingAverageCrossStrategy(short_window=5, long_window=20)
        assert strategy.name == "MA_Cross_5_20"
