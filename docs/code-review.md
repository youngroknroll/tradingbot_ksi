# 코드 리뷰 보고서

> 리뷰 일자: 2026-04-13
> 리뷰어: 금융 시스템 코드 리뷰어 (AI)
> 대상: tradingbot 전체 코드베이스 (기본 설계 완료 시점)

---

## 1. 총평

아키텍처 설계는 양호하다. 도메인 분리(strategy / risk / execution / broker / portfolio), 브로커 추상화(ABC), 멱등성 키 기반 중복 주문 방지 등 금융 시스템에 필요한 핵심 구조가 갖춰져 있다.

그러나 **실거래(live) 모드 전환 전에 반드시 해결해야 할 결함이 다수 존재**한다. 아래 항목을 심각도 순으로 정리한다.

| 심각도 | 건수 | 의미 |
|--------|------|------|
| CRITICAL | 5 | 실거래 시 재무적 손실 또는 시스템 장애 직결 |
| HIGH | 5 | 데이터 정합성, 운영 안정성에 영향 |
| MEDIUM | 4 | 보안, 감사(audit), 성능 관련 |
| LOW | 2 | 코드 품질, 효율성 개선 |

---

## 2. CRITICAL (즉시 수정 필요)

### C-1. KIS 토큰 만료 미처리

- **파일**: `app/broker/kis_broker.py:21-38`
- **현상**: `_get_token()`이 한 번 발급받은 토큰을 만료 시점 체크 없이 무한 재사용한다.
- **영향**: KIS 토큰은 24시간 유효. 만료 후 모든 API 호출이 401 실패하며, 주문/조회가 전면 중단된다.
- **수정 방안**:
  ```python
  def __init__(self) -> None:
      self._access_token: str = ""
      self._token_expires_at: datetime | None = None

  async def _get_token(self) -> str:
      if self._access_token and self._token_expires_at and datetime.now() < self._token_expires_at:
          return self._access_token
      # 재발급 로직
  ```

### C-2. 실제 체결가/체결수량 미반영

- **파일**: `app/broker/kis_broker.py:75-80`
- **현상**: KIS API 응답의 실제 체결 데이터를 무시하고, 주문 요청 값(order.price, order.quantity)을 그대로 Fill에 넣는다.
- **영향**: 시장가 주문 시 실제 체결가와 괴리 발생. 포지션 평균단가, PnL 계산이 전부 부정확해진다. 금융 시스템에서 체결 데이터 부정확은 재무보고 오류로 직결된다.
- **수정 방안**: KIS API 응답에서 `output.ord_qty`(체결수량), `output.ord_unpr`(체결단가)를 파싱하여 Fill에 반영한다. 응답에 체결 정보가 없는 경우(비동기 체결) 별도 체결 조회 API를 호출해야 한다.

### C-3. 매도 주문 리스크 검증 누락

- **파일**: `app/paper_trading/service.py:68-74`
- **현상**: 매수(BUY)에만 `risk.validate_order()`를 호출하고, 매도(SELL)에는 리스크 체크 없이 바로 주문을 제출한다.
- **영향**: 비정상 매도(예: 보유 수량 초과 매도 시도, 일일 손실 한도 초과 상태에서의 매도)가 필터링되지 않는다.
- **수정 방안**: 매도 분기에도 `self._risk.validate_order(order, account, current_daily_loss)` 호출을 추가한다.

### C-4. 주문-체결-상태 업데이트 트랜잭션 원자성 미보장

- **파일**: `app/execution/service.py:24-54`
- **현상**: 주문 저장(save) -> 브로커 제출(submit) -> 상태 업데이트(update_status)가 각각 독립적인 DB 호출이다.
- **영향**: 브로커에서 체결 완료 후 상태 업데이트 전에 앱이 크래시하면, DB에는 PENDING이지만 실제로는 체결된 "고스트 주문"이 생긴다. 포지션과 실제 보유량 간 불일치 발생.
- **수정 방안**:
  - 단기: 주문 저장과 상태 업데이트를 하나의 DB 트랜잭션으로 묶는다.
  - 장기: 정기적인 reconciliation(대사) 로직을 추가하여 브로커 상태와 DB 상태를 비교/보정한다.

### C-5. API 인증/인가 완전 부재

- **파일**: `app/api/admin.py` 전체
- **현상**: `/api/health`, `/api/positions`, `/api/positions/{symbol}` 모든 엔드포인트에 인증 미들웨어가 없다.
- **영향**: 네트워크에 노출될 경우 누구나 포지션, 계좌 정보를 조회할 수 있다. 금융 데이터 유출 위험.
- **수정 방안**: 최소 API Key 기반 인증 미들웨어를 추가한다. 운영 환경에서는 JWT + RBAC을 권장한다.

---

## 3. HIGH (조기 수정 권장)

### H-1. order_id 자동 생성 없음

- **파일**: `app/domain/entities.py:34`, `app/execution/order_factory.py:14-25`
- **현상**: `Order.order_id`의 기본값이 빈 문자열(`""`)이고, `create_order_from_signal()`에서 UUID를 할당하지 않는다.
- **영향**: `OrderModel.order_id`에 unique 제약이 걸려 있으므로, 두 번째 주문부터 unique constraint 위반으로 INSERT 실패한다.
- **수정 방안**: `order_id: str = Field(default_factory=lambda: str(uuid.uuid4()))` 또는 팩토리에서 명시적으로 할당한다.

### H-2. Decimal/float 혼용 (정밀도 손실)

- **파일**: `app/risk/rules.py:52-53`, `app/domain/entities.py:30,72`
- **현상**: 금액 계산은 Decimal이지만, 손절 비율(`stop_loss_percent`)과 신호 강도(`strength`)가 float이다. 손절 판단 시 `float()` 변환을 거친다.
- **영향**: 극단적 가격(소수점 이하 정밀도가 중요한 경우)에서 부동소수점 오차로 손절이 발동하지 않을 수 있다.
- **수정 방안**: `stop_loss_percent`를 `Decimal`로 변경하고, 비교 연산을 Decimal끼리 수행한다.

### H-3. 날짜 하드코딩

- **파일**: `app/paper_trading/service.py:47-48`
- **현상**: `start_date="20260101"`, `end_date="20260413"`이 코드에 하드코딩되어 있다.
- **영향**: 시간이 지나면 의미 없는 데이터를 조회하거나, 최신 데이터를 가져오지 못한다.
- **수정 방안**: `datetime.now()` 기준으로 동적 계산한다. (예: 최근 60거래일)

### H-4. cancel_order 미구현

- **파일**: `app/broker/kis_broker.py:126-128`
- **현상**: `cancel_order()`가 항상 `False`를 반환하며 실제 취소 API를 호출하지 않는다.
- **영향**: 잘못된 주문이 나간 경우 시스템에서 취소할 수 없다. 실거래 환경에서 치명적이다.
- **수정 방안**: KIS 주문 취소 API (`TTTC0803U`)를 구현한다.

### H-5. Fill-Order 간 FK 관계 없음

- **파일**: `app/infra/db/models.py:49`
- **현상**: `FillModel.order_id`가 `OrderModel`에 대한 외래키(FK)가 아닌 단순 문자열 컬럼이다.
- **영향**: 존재하지 않는 주문에 대한 체결 레코드가 저장될 수 있어 데이터 정합성이 깨진다.
- **수정 방안**: `ForeignKey("orders.order_id")`를 추가하고, relationship을 정의한다.

---

## 4. MEDIUM

### M-1. datetime.now() 타임존 미지정

- **파일**: `app/domain/entities.py:42,50,59`, `app/broker/kis_broker.py:80`
- **현상**: `datetime.now()`에 타임존 인자가 없어 서버 로컬 타임존에 의존한다.
- **영향**: 서버 환경에 따라 시간이 달라지고, 클라우드 배포 시 UTC/KST 불일치가 발생한다. 금융 거래의 시간 기록은 감사(audit) 추적에 핵심이다.
- **수정 방안**: `datetime.now(tz=ZoneInfo("Asia/Seoul"))` 또는 UTC 통일 후 표시 시 KST 변환.

### M-2. Rate Limiting 부재

- **현상**: API 엔드포인트에 레이트 리미팅이 없고, KIS API 호출에도 속도 제한 로직이 없다.
- **영향**: KIS API 초당 호출 제한 초과 시 IP 차단 가능. API 엔드포인트는 DoS 공격에 취약하다.
- **수정 방안**: FastAPI 미들웨어로 레이트 리미팅 추가. KIS 호출에는 asyncio.Semaphore 또는 토큰 버킷 패턴 적용.

### M-3. 민감 정보 로깅 위험

- **파일**: `app/broker/kis_broker.py:38,69`
- **현상**: `BrokerConnectionError`, `BrokerError` 메시지에 `httpx.HTTPError` 전체를 포함하므로, HTTP 응답 본문(토큰, 계좌 정보 등)이 로그에 노출될 수 있다.
- **수정 방안**: 에러 메시지를 필터링하여 민감 정보를 제거한 후 로깅한다.

### M-4. 통합/E2E 테스트 부재

- **현상**: `tests/integration/`, `tests/e2e/` 디렉토리는 존재하나 테스트 파일이 없다.
- **영향**: DB 연동, 브로커 통신, 전체 주문 흐름 등 실제 동작을 검증할 수 없다.
- **수정 방안**: 최소한 DB 연동 통합 테스트와 주문-체결-포지션 업데이트 E2E 테스트를 작성한다.

---

## 5. LOW

### L-1. httpx.AsyncClient 매 요청마다 생성

- **파일**: `app/broker/kis_broker.py:31,63,108`
- **현상**: 매번 `async with httpx.AsyncClient()` 로 새 클라이언트를 생성한다.
- **영향**: 커넥션 풀 재사용이 안 되어 성능이 저하된다.
- **수정 방안**: 클래스 초기화 시 `httpx.AsyncClient`를 한 번 생성하고, 종료 시 `aclose()` 한다.

### L-2. config.py 기본값에 자격증명 포함

- **파일**: `app/core/config.py:5`
- **현상**: `database_url` 기본값이 `"postgresql+asyncpg://user:password@localhost:5432/tradingbot"`이다.
- **영향**: `.env` 미설정 시 기본 자격증명으로 접속을 시도한다. 의도치 않은 DB 접근 가능.
- **수정 방안**: 기본값을 빈 문자열로 두고, 앱 시작 시 필수 환경변수 검증 로직을 추가한다.

---

## 6. 문서-코드 불일치

| 항목 | 문서 내용 | 실제 코드 | 위치 |
|------|-----------|-----------|------|
| Python 버전 | `architecture.md`: Python 3.9+ | `pyproject.toml`: Python 3.11+ | `docs/architecture.md:10` |
| API 경로 | `api-reference.md`: `/api/health` | 실제 라우터 prefix 확인 필요 (admin.py에 prefix 미지정) | `docs/api-reference.md`, `app/api/admin.py` |
| RiskRule.max_symbol_exposure | `domain-model.md`에 누락 | 엔티티에 `max_symbol_exposure` 필드 존재 | `app/domain/entities.py:71` |
| 테이블 생성 | `setup-guide.md`: "Alembic 마이그레이션 예정" | Alembic 설정 파일 부재 | `docs/setup-guide.md:47` |

---

## 7. 수정 우선순위 로드맵

### Phase 1 - 안전성 확보 (실거래 전 필수)

1. **C-1** KIS 토큰 만료 처리
2. **C-2** 실제 체결가 반영
3. **C-4** 트랜잭션 원자성 확보
4. **H-1** order_id UUID 자동 생성
5. **C-3** 매도 리스크 검증 추가

### Phase 2 - 보안 및 데이터 정합성

6. **C-5** API 인증 추가
7. **H-5** Fill-Order FK 관계 설정
8. **H-2** Decimal 통일
9. **M-1** 타임존 통일
10. **M-3** 로그 민감정보 필터링

### Phase 3 - 운영 안정성

11. **H-3** 날짜 동적 계산
12. **H-4** cancel_order 구현
13. **M-2** Rate Limiting 적용
14. **L-1** httpx 클라이언트 재사용
15. **L-2** config 기본값 정리

### Phase 4 - 품질 보증

16. **M-4** 통합/E2E 테스트 작성
17. 문서-코드 불일치 해소

---

## 8. 잘된 점

- **멱등성 설계**: SHA256 기반 idempotency_key로 중복 주문을 구조적으로 방지한다.
- **브로커 추상화**: `Broker` ABC를 통해 FakeBroker/KISBroker 교체가 깔끔하다.
- **도메인 분리**: strategy, risk, execution, portfolio가 명확히 분리되어 있어 각 모듈의 책임이 분명하다.
- **Pydantic 활용**: 도메인 엔티티에 Pydantic v2를 사용하여 타입 안전성과 직렬화를 확보했다.
- **구조화 로깅**: structlog 기반으로 이벤트명, 컨텍스트 변수를 포함한 로그를 남긴다.
- **리스크 룰 분리**: 개별 리스크 체크를 순수 함수로 분리하여 테스트와 조합이 용이하다.
- **Decimal 사용**: 금액 계산에 Decimal을 사용하여 부동소수점 오차를 방지했다 (일부 예외 존재).
