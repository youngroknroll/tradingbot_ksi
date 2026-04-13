# 시스템 아키텍처

## 개요

Python + FastAPI 기반 주식 자동매매 시스템. 터미널에서 동작하며, 백테스트/페이퍼트레이딩/실거래 3단계를 지원한다.

## 기술 스택

| 구분 | 기술 |
|------|------|
| 언어 | Python 3.9+ |
| 웹 프레임워크 | FastAPI |
| ORM | SQLAlchemy 2.0 (async) |
| DB | PostgreSQL (asyncpg) |
| HTTP 클라이언트 | httpx |
| 데이터 검증 | Pydantic v2 |
| 로깅 | structlog |
| 브로커 | 한국투자증권 (KIS) REST API |

## 모듈 구조

```
app/
├── core/           # 설정, 로깅, 예외
├── domain/         # 도메인 엔티티, 열거형
├── market_data/    # 시세 데이터 수집 (KIS API)
├── strategy/       # 매매 전략 (MA Cross 등)
├── risk/           # 리스크 관리 (포지션 크기, 손절)
├── execution/      # 주문 생성, 멱등성 보장
├── broker/         # 브로커 연동 (Fake, KIS)
├── portfolio/      # 포지션/PnL 관리
├── backtest/       # 백테스트 엔진
├── paper_trading/  # 모의 매매
├── monitoring/     # 헬스체크, 알림
├── infra/          # DB 연결, Repository
└── api/            # FastAPI 엔드포인트
```

## 데이터 흐름

```
Market Data (KIS API)
    ↓
Strategy (신호 계산)
    ↓
Risk Manager (검증)
    ↓
Execution (주문 생성 + 멱등성)
    ↓
Broker (주문 전송)
    ↓
Portfolio (포지션 업데이트)
```

## 실행 모드

| 모드 | 브로커 | 데이터 | 용도 |
|------|--------|--------|------|
| Backtest | 없음 (엔진 내부) | 과거/샘플 데이터 | 전략 검증 |
| Paper | FakeBroker | KIS 실시간 데이터 | 모의 매매 |
| Live | KISBroker | KIS 실시간 데이터 | 실거래 |

## 핵심 설계 원칙

1. **멱등성**: idempotency_key로 중복 주문 방지
2. **영속 상태**: 포지션/주문은 PostgreSQL에 저장
3. **안전 우선**: 리스크 체크 후에만 주문 실행
4. **전략 분리**: Strategy ABC로 전략 교체 가능
5. **브로커 추상화**: Broker ABC로 Fake/KIS 교체 가능
