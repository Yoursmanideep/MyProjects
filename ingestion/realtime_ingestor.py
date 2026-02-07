from __future__ import annotations

import time
from datetime import date, datetime

from ingestion.alpha_vantage import AlphaVantageClient


def _parse_price(value: str) -> float:
    price = float(value)
    if price < 0:
        raise ValueError("Negative price value")
    return price


def ingest_realtime_once(client: AlphaVantageClient, db, stocks, logger) -> None:
    for stock in stocks:
        try:
            series = client.fetch_intraday(stock.symbol)
            latest_timestamp, metrics = client.latest_timestamp(series)
            latest_datetime = datetime.fromisoformat(latest_timestamp)
            date_value = str(date.fromisoformat(latest_timestamp.split(" ")[0]))
            latest_date = db.latest_price_date(stock.stock_id)
            if latest_date and date.fromisoformat(date_value) <= latest_date:
                logger.info(
                    "Skipped realtime row for %s (latest date %s already ingested)",
                    stock.symbol,
                    latest_date,
                )
                continue
            row = (
                stock.stock_id,
                date_value,
                _parse_price(metrics["1. open"]),
                _parse_price(metrics["4. close"]),
                _parse_price(metrics["2. high"]),
                _parse_price(metrics["3. low"]),
                int(float(metrics["5. volume"])),
            )
            inserted = db.insert_stock_prices([row])
            if inserted:
                logger.info(
                    "Inserted realtime row for %s at %s", stock.symbol, latest_datetime
                )
            else:
                logger.info(
                    "Skipped duplicate realtime row for %s at %s", stock.symbol, latest_datetime
                )
        except Exception as exc:
            logger.exception("Realtime ingestion failure for %s: %s", stock.symbol, exc)


def ingest_realtime(
    client: AlphaVantageClient,
    db,
    stocks,
    logger,
    interval_seconds: int = 60,
) -> None:
    while True:
        ingest_realtime_once(client=client, db=db, stocks=stocks, logger=logger)
        time.sleep(interval_seconds)
