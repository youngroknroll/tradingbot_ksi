# 도메인 모델

## 엔티티

### Stock
주식 종목 정보.

| 필드 | 타입 | 설명 |
|------|------|------|
| symbol | str | 종목코드 (예: 005930) |
| market | str | 시장 (기본: KRX) |
| name | str | 종목명 |

### Candle
OHLCV 봉 데이터.

| 필드 | 타입 | 설명 |
|------|------|------|
| symbol | str | 종목코드 |
| timestamp | datetime | 시간 |
| open | Decimal | 시가 |
| high | Decimal | 고가 |
| low | Decimal | 저가 |
| close | Decimal | 종가 |
| volume | int | 거래량 |

### Signal
매매 신호.

| 필드 | 타입 | 설명 |
|------|------|------|
| symbol | str | 종목코드 |
| timestamp | datetime | 신호 발생 시간 |
| action | SignalAction | BUY / SELL / HOLD |
| reason | str | 신호 근거 |
| strength | float | 신호 강도 (0.0~1.0) |

### Order
주문.

| 필드 | 타입 | 설명 |
|------|------|------|
| order_id | str | 주문 ID |
| symbol | str | 종목코드 |
| side | OrderSide | BUY / SELL |
| quantity | int | 주문 수량 |
| price | Decimal | 주문 가격 |
| order_type | OrderType | MARKET / LIMIT |
| status | OrderStatus | PENDING → SUBMITTED → FILLED |
| idempotency_key | str | 멱등성 키 (중복 방지) |

### Fill
체결.

| 필드 | 타입 | 설명 |
|------|------|------|
| fill_id | str | 체결 ID |
| order_id | str | 주문 ID |
| filled_quantity | int | 체결 수량 |
| filled_price | Decimal | 체결 가격 |

### Position
포지션.

| 필드 | 타입 | 설명 |
|------|------|------|
| symbol | str | 종목코드 |
| quantity | int | 보유 수량 |
| average_price | Decimal | 평균 매입가 |
| realized_pnl | Decimal | 실현 손익 |
| unrealized_pnl | Decimal | 미실현 손익 |

### RiskRule
리스크 규칙.

| 필드 | 타입 | 기본값 | 설명 |
|------|------|--------|------|
| max_position_size | Decimal | 1,000,000 | 최대 포지션 금액 |
| max_daily_loss | Decimal | 50,000 | 일일 최대 손실 |
| stop_loss_percent | float | 3.0 | 손절 비율 (%) |

## 열거형 (Enums)

- **SignalAction**: BUY, SELL, HOLD
- **OrderSide**: BUY, SELL
- **OrderType**: MARKET, LIMIT
- **OrderStatus**: PENDING, SUBMITTED, FILLED, PARTIALLY_FILLED, CANCELLED, REJECTED
- **TradingMode**: backtest, paper, live
