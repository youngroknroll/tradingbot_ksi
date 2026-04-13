# API 레퍼런스

## 엔드포인트

### GET /api/health
시스템 상태 확인.

**응답 예시:**
```json
{
  "status": "healthy",
  "timestamp": "2026-04-13T12:00:00",
  "checks": {
    "database": "ok"
  }
}
```

### GET /api/positions
전체 보유 포지션 조회.

**응답 예시:**
```json
[
  {
    "symbol": "005930",
    "quantity": 10,
    "average_price": "55000.00",
    "realized_pnl": "5000.00",
    "unrealized_pnl": "3000.00"
  }
]
```

### GET /api/positions/{symbol}
특정 종목 포지션 조회.

**파라미터:**
- `symbol`: 종목코드 (예: 005930)

**응답 예시:**
```json
{
  "symbol": "005930",
  "quantity": 10,
  "average_price": "55000.00",
  "realized_pnl": "5000.00",
  "unrealized_pnl": "3000.00"
}
```

## 서버 실행

```bash
# CLI로 실행
python -m app.cli server --port 8000

# 또는 직접 실행
python main.py
```
