from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://user:password@localhost:5432/tradingbot"

    kis_app_key: str = ""
    kis_app_secret: str = ""
    kis_account_number: str = ""
    kis_base_url: str = "https://openapivts.koreainvestment.com:9443"
    kis_is_paper: bool = True

    trading_mode: str = "paper"
    max_position_size: int = 1_000_000
    max_daily_loss: int = 50_000
    stop_loss_percent: float = 3.0

    log_level: str = "INFO"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
