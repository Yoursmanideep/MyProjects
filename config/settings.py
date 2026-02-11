import os
from dataclasses import dataclass


@dataclass(frozen=True)
class MySQLConfig:
    host: str
    port: int
    database: str
    user: str
    password: str


@dataclass(frozen=True)
class AlphaVantageConfig:
    api_key: str
    base_url: str = "https://www.alphavantage.co/query"
    max_retries: int = 5
    backoff_seconds: float = 5.0
    min_interval_seconds: float = 12.0


@dataclass(frozen=True)
class AppConfig:
    mysql: MySQLConfig
    alphavantage: AlphaVantageConfig
    log_file: str
    batch_size: int
    historical_years: int
    pool_size: int
    realtime_interval_seconds: int
    restart_backoff_seconds: int


def load_config() -> AppConfig:
    mysql_config = MySQLConfig(
        host=os.getenv("MYSQL_HOST", "localhost"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        database=os.getenv("MYSQL_DATABASE", "StockAnalyticsDB"),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", "123456789"),
    )
    api_key = os.getenv("ALPHAVANTAGE_API_KEY")
    if not api_key:
        raise EnvironmentError("ALPHAVANTAGE_API_KEY is required")
    alphavantage_config = AlphaVantageConfig(
        api_key=api_key,
        max_retries=int(os.getenv("ALPHAVANTAGE_MAX_RETRIES", "5")),
        backoff_seconds=float(os.getenv("ALPHAVANTAGE_BACKOFF_SECONDS", "5")),
        min_interval_seconds=float(os.getenv("ALPHAVANTAGE_MIN_INTERVAL_SECONDS", "12")),
    )
    return AppConfig(
        mysql=mysql_config,
        alphavantage=alphavantage_config,
        log_file=os.getenv("INGESTION_LOG_FILE", "logs/ingestion.log"),
        batch_size=int(os.getenv("HISTORICAL_BATCH_SIZE", "1000")),
        historical_years=int(os.getenv("HISTORICAL_YEARS", "5")),
        pool_size=int(os.getenv("MYSQL_POOL_SIZE", "5")),
        realtime_interval_seconds=int(os.getenv("REALTIME_INTERVAL_SECONDS", "60")),
        restart_backoff_seconds=int(os.getenv("RESTART_BACKOFF_SECONDS", "30")),
    )
