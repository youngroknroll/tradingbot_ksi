# plan.md

# 주식 트레이딩 봇 MVP 개발 계획

## 1. 목표

주식 트레이딩 봇의 1차 목표는 “수익 극대화”가 아니다.  
우선은 다음을 만족하는 **안전한 자동매매 MVP**를 만드는 것을 목표로 한다.

- 사전에 정의된 전략 규칙에 따라 매수/매도 신호를 계산할 수 있다.
- 주문 요청이 중복 실행되지 않는다.
- 현재 포지션과 주문 상태를 일관되게 관리할 수 있다.
- 예외 상황(API 실패, 미체결, 장 종료 등)에 대해 안전하게 동작한다.
- 실거래 이전에 백테스트 및 페이퍼 트레이딩으로 검증 가능하다.

---

## 2. 범위

### 이번 MVP에서 포함할 것

- 단일 전략 1개
- 소수 종목 대상 거래
- 시세 데이터 조회
- 신호 계산
- 주문 생성
- 주문/포지션 저장
- 리스크 관리
- 로그 기록
- 알림 전송
- 백테스트
- 페이퍼 트레이딩

### 이번 MVP에서 제외할 것

- 다중 전략 조합
- 고빈도 트레이딩
- 복잡한 포트폴리오 최적화
- 머신러닝 기반 예측 모델
- 초저지연 인프라
- 멀티 브로커 통합
- 자동 재학습 AI 전략

---

## 3. 핵심 원칙

### 3.1 전략보다 안정성을 우선한다
트레이딩 시스템은 “좋은 매수 신호”보다 “치명적 오동작 방지”가 더 중요하다.

### 3.2 실거래 전에 반드시 시뮬레이션을 거친다
구현 순서는 다음과 같다.

1. 백테스트
2. 페이퍼 트레이딩
3. 소액 실거래

### 3.3 주문 실행은 반드시 멱등적으로 처리한다
같은 주문 의도가 여러 번 들어와도 실제 주문은 한 번만 생성되어야 한다.

### 3.4 상태 저장을 신뢰 가능한 기준으로 삼는다
현재 포지션, 주문 상태, 체결 여부는 메모리가 아니라 영속 저장소를 기준으로 판단한다.

### 3.5 작은 단위로 테스트하며 확장한다
전략, 리스크 관리, 주문 실행, 상태 전이 로직을 분리하고 각각 독립적으로 검증 가능하게 만든다.

---

## 4. 대상 시스템 개요

시스템은 아래 구성요소로 나눈다.

- `market_data`: 시세 데이터 수집
- `strategy`: 매수/매도 신호 계산
- `risk`: 포지션 크기 및 손실 제한 판단
- `execution`: 주문 생성 및 브로커 전송
- `portfolio`: 보유 포지션 관리
- `broker`: 증권사 API 연동
- `storage`: 주문, 체결, 포지션, 로그 저장
- `backtest`: 과거 데이터 기반 전략 검증
- `paper_trading`: 실시간 모의 실행
- `monitoring`: 알림, 장애 감지, 운영 로그

---

## 5. 도메인 모델 초안

### Stock
- symbol
- market
- name

### Candle
- symbol
- timestamp
- open
- high
- low
- close
- volume

### Signal
- symbol
- timestamp
- action (BUY | SELL | HOLD)
- reason

### Order
- order_id
- symbol
- side
- quantity
- price
- order_type
- status
- idempotency_key
- created_at

### Fill
- fill_id
- order_id
- filled_quantity
- filled_price
- filled_at

### Position
- symbol
- quantity
- average_price
- realized_pnl
- unrealized_pnl
- updated_at

### Account
- cash_balance
- total_equity
- available_buying_power

### RiskRule
- max_position_size
- max_daily_loss
- max_symbol_exposure
- stop_loss_percent

---

## 6. 디렉토리 구조 초안

```text
app/
├── core/
│   ├── config.py
│   ├── exceptions.py
│   └── logging.py
├── domain/
│   ├── entities/
│   ├── enums.py
│   └── dto.py
├── market_data/
│   ├── service.py
│   └── repository.py
├── strategy/
│   ├── base.py
│   ├── moving_average.py
│   └── service.py
├── risk/
│   ├── service.py
│   └── rules.py
├── execution/
│   ├── service.py
│   └── order_factory.py
├── broker/
│   ├── base.py
│   ├── fake_broker.py
│   └── real_broker.py
├── portfolio/
│   ├── service.py
│   └── calculator.py
├── backtest/
│   ├── engine.py
│   └── metrics.py
├── paper_trading/
│   └── service.py
├── monitoring/
│   ├── notifier.py
│   └── healthcheck.py
├── infra/
│   ├── db/
│   └── repositories/
└── api/
    └── admin.py

tests/
├── unit/
├── integration/
└── e2e/
