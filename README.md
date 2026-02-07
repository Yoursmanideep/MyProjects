# Stock Data Ingestion Pipeline

Production-grade Python pipeline for loading historical daily stock prices and ingesting realtime minute data into MySQL with an orchestrated runtime controller.

## Features
- MySQL connectivity with index management for large datasets.
- Historical load for the past 5 years using Alpha Vantage daily data.
- Realtime ingestion every minute using Alpha Vantage intraday data.
- Duplicate prevention with unique index and INSERT IGNORE.
- Robust logging of inserts, skipped duplicates, and API failures.
- Orchestrator for one-time historical load, continuous realtime updates, and automatic restarts.

## Project Structure
```
/config
  settings.py
/database
  db.py
/ingestion
  alpha_vantage.py
  historical_loader.py
  realtime_ingestor.py
  orchestrator.py
/logging
  log_config.py
/main.py
```

## Requirements
- Python 3.9+
- MySQL server
- Alpha Vantage API key

## Installation
```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configuration
Set environment variables before running:

```
export MYSQL_HOST=localhost
export MYSQL_PORT=3306
export MYSQL_DATABASE=StockAnalyticsDB
export MYSQL_USER=root
export MYSQL_PASSWORD=123456789
export ALPHAVANTAGE_API_KEY=your_api_key
```

Optional overrides:
```
export HISTORICAL_YEARS=5
export HISTORICAL_BATCH_SIZE=1000
export ALPHAVANTAGE_MAX_RETRIES=5
export ALPHAVANTAGE_BACKOFF_SECONDS=5
export ALPHAVANTAGE_MIN_INTERVAL_SECONDS=12
export INGESTION_LOG_FILE=logs/ingestion.log
export MYSQL_POOL_SIZE=5
export REALTIME_INTERVAL_SECONDS=60
export RESTART_BACKOFF_SECONDS=30
```

## Usage
```
python main.py
```

## Notes
- The pipeline assumes your MySQL schema already contains the `Stocks`, `Calendar`, and `StockPrices` tables.
- A unique index on `(StockID, DateValue)` is created automatically if it does not already exist.
- The orchestrator records historical load completion in `IngestionState` to avoid reloading on restarts.
- Realtime ingestion uses the latest 1-minute data point and inserts one row per date in `StockPrices` to match the existing schema.

## Logging
Logs are written to `logs/ingestion.log` and stdout.
