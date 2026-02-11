from __future__ import annotations

from datetime import date, timedelta
from typing import Iterable, List, Optional, Tuple

from ingestion.alpha_vantage import AlphaVantageClient


def _parse_price(value: str) -> float:
    return float(value)


def build_historical_rows(
    stock_id: int,
    series: dict,
    years: int,
    latest_date: Optional[date],
) -> List[Tuple[int, str, float, float, float, float, int]]:
    cutoff = date.today() - timedelta(days=365 * years)
    rows: List[Tuple[int, str, float, float, float, float, int]] = []
    for date_value, metrics in series.items():
        parsed_date = date.fromisoformat(date_value)
        if parsed_date < cutoff:
            continue
        if latest_date and parsed_date <= latest_date:
            continue
        rows.append(
            (
                stock_id,
                date_value,
                _parse_price(metrics["1. open"]),
                _parse_price(metrics["4. close"]),
                _parse_price(metrics["2. high"]),
                _parse_price(metrics["3. low"]),
                int(metrics["6. volume"]),
            )
        )
    return rows


def chunked(rows: List[Tuple], size: int) -> Iterable[List[Tuple]]:
    for idx in range(0, len(rows), size):
        yield rows[idx : idx + size]


def load_historical_data(
    client: AlphaVantageClient,
    db,
    stocks,
    years: int,
    batch_size: int,
    logger,
) -> None:
    for stock in stocks:
        logger.info("Loading historical data for %s", stock.symbol)
        latest_date = db.latest_price_date(stock.stock_id)
        if latest_date:
            logger.info("Latest stored date for %s is %s", stock.symbol, latest_date)
        series = client.fetch_daily(stock.symbol)
        rows = build_historical_rows(stock.stock_id, series, years, latest_date)
        if not rows:
            logger.info("No historical gaps for %s", stock.symbol)
            continue
        inserted_total = 0
        for batch in chunked(rows, batch_size):
            inserted = db.insert_stock_prices(batch)
            inserted_total += inserted
            logger.info(
                "Inserted %s rows (batch) for %s", inserted, stock.symbol
            )
        skipped = len(rows) - inserted_total
        if skipped > 0:
            logger.info("Skipped %s duplicate rows for %s", skipped, stock.symbol)
