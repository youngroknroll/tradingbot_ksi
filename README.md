# Trading Bot

Python + FastAPI 기반 주식 자동매매 시스템. 한국투자증권(KIS) API를 사용하여 백테스트, 모의매매, 실거래를 지원한다.

## 작동 방식

### 전체 흐름

```
시세 수집 (KIS API)
    |
    v
전략 평가 (이동평균 교차)
    |
    v
리스크 검증 (포지션 크기, 일일 손실, 매수력, 손절)
    |
    v
주문 생성 (멱등성 키로 중복 방지)
    |
    v
브로커 제출 (KIS API 또는 FakeBroker)
    |
    v
포지션 업데이트 (평균단가, 실현/미실현 PnL)
```

### 실행 모드

| 모드 | 브로커 | 데이터 | 용도 |
|------|--------|--------|------|
| **Backtest** | 내부 엔진 | 샘플/과거 데이터 | 전략 성과 검증 |
| **Paper** | FakeBroker | KIS 실시간 시세 | 실제 돈 없이 모의매매 |
| **Live** | KISBroker | KIS 실시간 시세 | 실제 주문 실행 |

### 매매 전략: 이동평균 교차 (MA Cross)

단기 이동평균(기본 5일)이 장기 이동평균(기본 20일)을 위로 돌파하면 매수(골든크로스), 아래로 돌파하면 매도(데드크로스).

```
골든크로스 (단기MA가 장기MA 상향 돌파) -> BUY
데드크로스 (단기MA가 장기MA 하향 돌파) -> SELL
교차 없음                             -> HOLD
```

### 리스크 관리

주문 실행 전 4가지 규칙을 검증한다. 하나라도 위반 시 주문이 차단된다.

| 규칙 | 기본값 | 설명 |
|------|--------|------|
| 최대 포지션 크기 | 1,000,000원 | 단일 주문 금액 한도 |
| 일일 최대 손실 | 50,000원 | 당일 누적 손실 한도 |
| 매수력 검증 | 계좌 잔고 | 잔고 초과 매수 방지 |
| 손절 | 3% | 평균단가 대비 3% 이상 하락 시 매도 |

### 멱등성 (중복 주문 방지)

`SHA256(종목코드:매수/매도:YYYYMMDDHHMM)` 해시로 idempotency key를 생성한다. 같은 종목에 같은 방향으로 같은 분(minute)에 중복 주문이 불가능하다.

## 프로젝트 구조

```
app/
├── api/            # FastAPI 엔드포인트 + 인증
├── backtest/       # 백테스트 엔진 + 성과 지표
├── broker/         # 브로커 추상화 (KIS, Fake)
├── core/           # 설정, 로깅, 예외
├── domain/         # 엔티티, 열거형
├── execution/      # 주문 생성 + 멱등성
├── infra/          # DB 연결, Repository
├── market_data/    # KIS 시세 API
├── monitoring/     # 헬스체크
├── paper_trading/  # 모의매매 서비스
├── portfolio/      # 포지션/PnL 관리
├── risk/           # 리스크 규칙
└── strategy/       # 매매 전략 (MA Cross)
```

## 기술 스택

| 구분 | 기술 |
|------|------|
| 언어 | Python 3.9+ |
| 웹 | FastAPI + Uvicorn |
| DB | PostgreSQL + SQLAlchemy 2.0 (async) |
| HTTP | httpx (async) |
| 검증 | Pydantic v2 |
| 로깅 | structlog |
| 브로커 | 한국투자증권 KIS REST API |

## 설치

```bash
pip install -e ".[dev]"
```

## 환경변수

```bash
cp .env.example .env
```

`.env` 파일에 다음 값을 설정한다:

| 변수 | 필수 | 설명 |
|------|------|------|
| `DATABASE_URL` | O | PostgreSQL 연결 URL |
| `KIS_APP_KEY` | O | KIS API 앱 키 |
| `KIS_APP_SECRET` | O | KIS API 시크릿 |
| `KIS_ACCOUNT_NUMBER` | O | 계좌번호 (예: 1234567801) |
| `API_KEY` | - | API 인증 키 (미설정 시 인증 비활성화) |
| `KIS_IS_PAPER` | - | 모의투자 여부 (기본: true) |

## 실행

### 백테스트 (샘플 데이터)

```bash
python -m app.cli backtest --symbol 005930 --short 5 --long 20
```

출력 예시:
```
=== Backtest Results ===
Total Return: +12.34%
Total Trades: 8
Win/Loss: 5/3
Win Rate: 62.5%
Max Drawdown: 4.56%
Sharpe Ratio: 1.23
Profit Factor: 2.10
```

### API 서버

```bash
python -m app.cli server --port 8000
```

### API 엔드포인트

모든 엔드포인트는 `X-API-Key` 헤더가 필요하다 (`API_KEY` 환경변수 설정 시).

```bash
# 헬스체크
curl -H "X-API-Key: your_key" http://localhost:8000/api/health

# 전체 포지션 조회
curl -H "X-API-Key: your_key" http://localhost:8000/api/positions

# 특정 종목 포지션
curl -H "X-API-Key: your_key" http://localhost:8000/api/positions/005930
```

## 테스트

```bash
# 전체 유닛 테스트
python -m pytest tests/unit/ -v

# 커버리지 포함
python -m pytest tests/unit/ --cov=app --cov-report=term-missing
```

## DB 설정 (Docker)

```bash
docker run -d --name tradingbot-db \
  -e POSTGRES_USER=user \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=tradingbot \
  -p 5432:5432 \
  postgres:16
```

## 새 전략 추가

`app/strategy/base.py`의 `Strategy` ABC를 상속한다:

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
