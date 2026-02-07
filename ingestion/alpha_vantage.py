from __future__ import annotations

import time
from datetime import datetime
from typing import Dict, Tuple

import requests

from config.settings import AlphaVantageConfig


class AlphaVantageClient:
    def __init__(self, config: AlphaVantageConfig, logger) -> None:
        self._config = config
        self._logger = logger
        self._last_call = 0.0

    def _throttle(self) -> None:
        elapsed = time.time() - self._last_call
        if elapsed < self._config.min_interval_seconds:
            time.sleep(self._config.min_interval_seconds - elapsed)
        self._last_call = time.time()

    def _request(self, params: Dict[str, str]) -> Dict:
        for attempt in range(1, self._config.max_retries + 1):
            self._throttle()
            response = requests.get(self._config.base_url, params=params, timeout=30)
            if response.status_code != 200:
                self._logger.warning(
                    "Alpha Vantage API failure status=%s attempt=%s", response.status_code, attempt
                )
                time.sleep(self._config.backoff_seconds * attempt)
                continue
            payload = response.json()
            if "Note" in payload or "Error Message" in payload:
                self._logger.warning(
                    "Alpha Vantage API limit or error attempt=%s message=%s",
                    attempt,
                    payload.get("Note") or payload.get("Error Message"),
                )
                time.sleep(self._config.backoff_seconds * attempt)
                continue
            return payload
        raise RuntimeError("Alpha Vantage API retries exhausted")

    def fetch_daily(self, symbol: str) -> Dict[str, Dict[str, str]]:
        payload = self._request(
            {
                "function": "TIME_SERIES_DAILY_ADJUSTED",
                "symbol": symbol,
                "outputsize": "full",
                "apikey": self._config.api_key,
            }
        )
        return payload.get("Time Series (Daily)", {})

    def fetch_intraday(self, symbol: str, interval: str = "1min") -> Dict[str, Dict[str, str]]:
        payload = self._request(
            {
                "function": "TIME_SERIES_INTRADAY",
                "symbol": symbol,
                "interval": interval,
                "outputsize": "compact",
                "apikey": self._config.api_key,
            }
        )
        key = f"Time Series ({interval})"
        return payload.get(key, {})

    @staticmethod
    def latest_timestamp(series: Dict[str, Dict[str, str]]) -> Tuple[str, Dict[str, str]]:
        if not series:
            raise ValueError("No data returned from Alpha Vantage")
        latest = max(series.keys(), key=lambda x: datetime.fromisoformat(x))
        return latest, series[latest]
