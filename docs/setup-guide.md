# 설치 및 실행 가이드

## 사전 요구사항

- Python 3.9+
- PostgreSQL (Docker 권장)
- 한국투자증권 API 키 (실거래/페이퍼 트레이딩 시)

## 1. 프로젝트 설치

```bash
# 프로젝트 클론
cd tradingbot

# 의존성 설치
pip install -e ".[dev]"
```

## 2. 환경변수 설정

```bash
cp .env.example .env
# .env 파일을 편집하여 실제 값 입력
```

### 필수 환경변수

| 변수 | 설명 | 예시 |
|------|------|------|
| DATABASE_URL | PostgreSQL 연결 URL | postgresql+asyncpg://user:pass@localhost:5432/tradingbot |
| KIS_APP_KEY | KIS API 앱 키 | (한국투자증권에서 발급) |
| KIS_APP_SECRET | KIS API 시크릿 | (한국투자증권에서 발급) |
| KIS_ACCOUNT_NUMBER | 계좌번호 | 12345678-01 |

## 3. 데이터베이스 설정

```bash
# PostgreSQL 실행 (Docker)
docker run -d --name tradingbot-db \
  -e POSTGRES_USER=user \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=tradingbot \
  -p 5432:5432 \
  postgres:16

# 테이블 생성 (Alembic 마이그레이션 예정)
```

## 4. 실행

### 백테스트 (샘플 데이터)
```bash
python -m app.cli backtest --symbol 005930 --short 5 --long 20
```

### API 서버
```bash
python -m app.cli server --port 8000
```

## 5. 테스트

```bash
# 전체 유닛 테스트
python -m pytest tests/unit/ -v

# 커버리지 포함
python -m pytest tests/unit/ --cov=app --cov-report=term-missing
```
