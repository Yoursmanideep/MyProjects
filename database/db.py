from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Iterable, List, Optional, Tuple

import mysql.connector
from mysql.connector import Error
from mysql.connector.pooling import MySQLConnectionPool

from config.settings import MySQLConfig


@dataclass(frozen=True)
class Stock:
    stock_id: int
    symbol: str
    company_name: str


class Database:
    def __init__(self, config: MySQLConfig, pool_size: int = 5) -> None:
        self._config = config
        self._pool = MySQLConnectionPool(
            pool_name="stock_ingestion_pool",
            pool_size=pool_size,
            host=self._config.host,
            port=self._config.port,
            database=self._config.database,
            user=self._config.user,
            password=self._config.password,
        )

    def connect(self):
        return self._pool.get_connection()

    def validate_connection(self) -> None:
        with self.connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()

    def fetch_stocks(self) -> List[Stock]:
        query = "SELECT StockID, StockSymbol, CompanyName FROM Stocks"
        with self.connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()
        return [Stock(stock_id=row[0], symbol=row[1], company_name=row[2]) for row in rows]

    def ensure_indexes(self) -> None:
        statements = [
            "CREATE INDEX idx_stockprices_stockid ON StockPrices (StockID)",
            "CREATE INDEX idx_stockprices_date ON StockPrices (DateValue)",
            "CREATE UNIQUE INDEX uq_stockprices_stockid_date ON StockPrices (StockID, DateValue)",
        ]
        with self.connect() as conn:
            with conn.cursor() as cursor:
                for stmt in statements:
                    try:
                        cursor.execute(stmt)
                    except Error:
                        continue
            conn.commit()

    def ensure_state_table(self) -> None:
        statement = (
            "CREATE TABLE IF NOT EXISTS IngestionState ("
            "StateKey VARCHAR(50) PRIMARY KEY, "
            "StateValue VARCHAR(255) NOT NULL"
            ")"
        )
        with self.connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute(statement)
            conn.commit()

    def get_state(self, key: str) -> Optional[str]:
        query = "SELECT StateValue FROM IngestionState WHERE StateKey = %s"
        with self.connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (key,))
                row = cursor.fetchone()
                return row[0] if row else None

    def set_state(self, key: str, value: str) -> None:
        statement = (
            "INSERT INTO IngestionState (StateKey, StateValue) "
            "VALUES (%s, %s) "
            "ON DUPLICATE KEY UPDATE StateValue = VALUES(StateValue)"
        )
        with self.connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute(statement, (key, value))
            conn.commit()

    def insert_stock_prices(
        self, rows: Iterable[Tuple[int, str, float, float, float, float, int]]
    ) -> int:
        insert_sql = (
            "INSERT IGNORE INTO StockPrices "
            "(StockID, DateValue, OpenPrice, ClosePrice, HighPrice, LowPrice, Volume) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s)"
        )
        row_list = list(rows)
        if not row_list:
            return 0
        with self.connect() as conn:
            with conn.cursor() as cursor:
                cursor.executemany(insert_sql, row_list)
                conn.commit()
                return cursor.rowcount

    def stock_price_exists(self, stock_id: int, date_value: str) -> bool:
        query = (
            "SELECT 1 FROM StockPrices WHERE StockID = %s AND DateValue = %s LIMIT 1"
        )
        with self.connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (stock_id, date_value))
                return cursor.fetchone() is not None

    def latest_price_date(self, stock_id: int) -> Optional[date]:
        query = "SELECT MAX(DateValue) FROM StockPrices WHERE StockID = %s"
        with self.connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (stock_id,))
                row = cursor.fetchone()
                return row[0] if row and row[0] else None
