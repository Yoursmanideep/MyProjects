from config.settings import load_config
from database.db import Database
from ingestion.alpha_vantage import AlphaVantageClient
from ingestion.orchestrator import Orchestrator, OrchestratorConfig
from logging.log_config import configure_logging


def main() -> None:
    config = load_config()
    logger = configure_logging(config.log_file)
    logger.info("Starting stock ingestion pipeline")

    db = Database(config.mysql, pool_size=config.pool_size)
    db.ensure_indexes()
    stocks = db.fetch_stocks()
    if not stocks:
        logger.error("No stocks found in Stocks table")
        return

    client = AlphaVantageClient(config.alphavantage, logger)

    orchestrator = Orchestrator(
        db=db,
        client=client,
        stocks=stocks,
        logger=logger,
        config=OrchestratorConfig(
            historical_years=config.historical_years,
            batch_size=config.batch_size,
            realtime_interval_seconds=config.realtime_interval_seconds,
            restart_backoff_seconds=config.restart_backoff_seconds,
        ),
    )
    orchestrator.run()


if __name__ == "__main__":
    main()
