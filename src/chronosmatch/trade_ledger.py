
import sqlite3
from pathlib import Path


class TradeLedger:
    """Persistent SQLite storage for completed ChronosMatch trades."""

    def __init__(self, db_path="data/chronosmatch.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self.connection = sqlite3.connect(self.db_path)

        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                trade_id INTEGER PRIMARY KEY AUTOINCREMENT,
                buy_order_id INTEGER NOT NULL,
                sell_order_id INTEGER NOT NULL,
                price INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                timestamp_ns INTEGER NOT NULL
            )
        """)

        self.connection.commit()

    def record_trade(self, trade, timestamp_ns):
        """Insert one completed trade."""
        buy_id, sell_id, price, quantity = trade

        self.connection.execute(
            """
            INSERT INTO trades (
                buy_order_id,
                sell_order_id,
                price,
                quantity,
                timestamp_ns
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (buy_id, sell_id, price, quantity, timestamp_ns),
        )

    def record_trades(self, trades, timestamp_ns):
        """Insert a batch of completed trades."""
        rows = [
            (buy_id, sell_id, price, quantity, timestamp_ns)
            for buy_id, sell_id, price, quantity in trades
        ]

        if rows:
            self.connection.executemany(
                """
                INSERT INTO trades (
                    buy_order_id,
                    sell_order_id,
                    price,
                    quantity,
                    timestamp_ns
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                rows,
            )

    def commit(self):
        self.connection.commit()

    def count_trades(self):
        cursor = self.connection.execute(
            "SELECT COUNT(*) FROM trades"
        )
        return cursor.fetchone()[0]

    def get_recent_trades(self, limit=10):
        cursor = self.connection.execute(
            """
            SELECT buy_order_id, sell_order_id, price,
                   quantity, timestamp_ns
            FROM trades
            ORDER BY trade_id DESC
            LIMIT ?
            """,
            (limit,),
        )
        return cursor.fetchall()

    def close(self):
        self.connection.commit()
        self.connection.close()
