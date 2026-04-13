# 전략 가이드

## 이동평균 교차 전략 (MA Cross)

### 개념

일상적인 비유: 날씨 예보와 비슷하다. 최근 5일 평균 기온(단기 이동평균)이 20일 평균 기온(장기 이동평균)을 넘어서면 "더워지는 추세"로 판단하는 것과 같다.

기술적으로는, 단기 이동평균선이 장기 이동평균선을 위로 돌파(골든크로스)하면 매수, 아래로 돌파(데드크로스)하면 매도 신호를 발생시키는 추세 추종 전략이다.

### 파라미터

| 파라미터 | 기본값 | 설명 |
|----------|--------|------|
| short_window | 5 | 단기 이동평균 기간 (일) |
| long_window | 20 | 장기 이동평균 기간 (일) |

### 신호 규칙

| 조건 | 신호 | 이름 |
|------|------|------|
| 이전: 단기MA <= 장기MA, 현재: 단기MA > 장기MA | BUY | 골든크로스 |
| 이전: 단기MA >= 장기MA, 현재: 단기MA < 장기MA | SELL | 데드크로스 |
| 그 외 | HOLD | - |

### 사용 예시

```python
from app.strategy.moving_average import MovingAverageCrossStrategy

# 기본 설정 (5일/20일)
strategy = MovingAverageCrossStrategy()

# 커스텀 설정 (10일/50일)
strategy = MovingAverageCrossStrategy(short_window=10, long_window=50)

# 신호 계산
signal = strategy.compute_signal(candles)
```

### 백테스트 실행

```bash
# 기본 (5일/20일)
python -m app.cli backtest --symbol 005930

# 커스텀 윈도우
python -m app.cli backtest --symbol 005930 --short 10 --long 50
```

### 백테스트 지표

| 지표 | 설명 |
|------|------|
| Total Return | 총 수익률 (%) |
| Win Rate | 승률 (%) |
| Max Drawdown | 최대 낙폭 (%) |
| Sharpe Ratio | 샤프 비율 (위험 대비 수익) |
| Profit Factor | 수익 팩터 (총이익/총손실) |

### 새 전략 추가 방법

1. `app/strategy/base.py`의 `Strategy` ABC를 상속
2. `name`, `compute_signal()`, `min_candles_required()` 구현
3. `app/strategy/` 디렉토리에 파일 추가

```python
from app.strategy.base import Strategy

class MyStrategy(Strategy):
    @property
    def name(self) -> str:
        return "MyStrategy"

    def min_candles_required(self) -> int:
        return 30

    def compute_signal(self, candles):
        # 신호 계산 로직
        ...
```
