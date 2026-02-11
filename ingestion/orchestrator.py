from __future__ import annotations

import signal
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Callable

from database.db import Database
from ingestion.alpha_vantage import AlphaVantageClient
from ingestion.historical_loader import load_historical_data
from ingestion.realtime_ingestor import ingest_realtime_once


@dataclass
class OrchestratorConfig:
    historical_years: int
    batch_size: int
    realtime_interval_seconds: int
    restart_backoff_seconds: int


class Orchestrator:
    def __init__(
        self,
        db: Database,
        client: AlphaVantageClient,
        stocks,
        logger,
        config: OrchestratorConfig,
    ) -> None:
        self._db = db
        self._client = client
        self._stocks = stocks
        self._logger = logger
        self._config = config
        self._stop_event = threading.Event()

    def _register_signal_handlers(self) -> None:
        def handler(signum, frame):
            self._logger.info("Shutdown signal received: %s", signum)
            self._stop_event.set()

        signal.signal(signal.SIGTERM, handler)
        signal.signal(signal.SIGINT, handler)

    def _with_restart(self, step: Callable[[], None], name: str) -> None:
        while not self._stop_event.is_set():
            try:
                step()
                return
            except Exception as exc:
                self._logger.exception("%s failed: %s", name, exc)
                self._logger.info(
                    "Restarting %s after %s seconds",
                    name,
                    self._config.restart_backoff_seconds,
                )
                time.sleep(self._config.restart_backoff_seconds)

    def _run_historical_once(self) -> None:
        self._db.validate_connection()
        self._db.ensure_state_table()
        state = self._db.get_state("historical_loaded")
        if state == "true":
            self._logger.info("Historical load already completed. Skipping.")
            return
        self._logger.info("Starting historical load")
        load_historical_data(
            client=self._client,
            db=self._db,
            stocks=self._stocks,
            years=self._config.historical_years,
            batch_size=self._config.batch_size,
            logger=self._logger,
        )
        self._db.set_state("historical_loaded", "true")
        self._logger.info("Historical load completed")

    def _run_realtime_forever(self) -> None:
        self._logger.info("Starting realtime ingestion loop")
        while not self._stop_event.is_set():
            try:
                self._db.validate_connection()
                ingest_realtime_once(
                    client=self._client,
                    db=self._db,
                    stocks=self._stocks,
                    logger=self._logger,
                )
                self._logger.info("Realtime ingestion cycle completed at %s", datetime.utcnow().isoformat())
                self._stop_event.wait(self._config.realtime_interval_seconds)
            except Exception as exc:
                self._logger.exception("Realtime ingestion loop failed: %s", exc)
                self._logger.info(
                    "Retrying realtime loop after %s seconds",
                    self._config.restart_backoff_seconds,
                )
                time.sleep(self._config.restart_backoff_seconds)

    def run(self) -> None:
        self._register_signal_handlers()
        self._logger.info("Orchestrator started at %s", datetime.utcnow().isoformat())
        self._with_restart(self._run_historical_once, "historical loader")
        if not self._stop_event.is_set():
            self._with_restart(self._run_realtime_forever, "realtime ingestion")
        self._logger.info("Orchestrator stopped")
