
import asyncio
import time

from chronosmatch.trade_ledger import TradeLedger


class AsyncTradeLedger:
    """Background worker that writes completed trades to SQLite in batches."""

    def __init__(self, db_path="data/chronosmatch.db",
                 batch_size=100, flush_interval=0.25):
        self.ledger = TradeLedger(db_path)
        self.queue = asyncio.Queue()
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.worker_task = None
        self._closed = False

    async def start(self):
        """Start the background database writer."""
        if self.worker_task is not None:
            raise RuntimeError("Ledger worker is already running")

        self.worker_task = asyncio.create_task(self._worker())

    async def submit(self, trade):
        """Queue one completed trade without writing to SQLite."""
        if self._closed:
            raise RuntimeError("Ledger is closed")

        if self.worker_task is None:
            raise RuntimeError("Start the ledger before submitting trades")

        await self.queue.put((trade, time.perf_counter_ns()))

    async def _worker(self):
        """Collect trades and write them in batches."""
        batch = []

        try:
            while True:
                try:
                    item = await asyncio.wait_for(
                        self.queue.get(),
                        timeout=self.flush_interval,
                    )
                    batch.append(item)

                except asyncio.TimeoutError:
                    pass

                if len(batch) >= self.batch_size or (
                    batch and self.queue.empty()
                ):
                    self._write_batch(batch)
                    for _ in batch:
                        self.queue.task_done()
                    batch.clear()

                if self._closed and self.queue.empty():
                    break

            if batch:
                self._write_batch(batch)
                for _ in batch:
                    self.queue.task_done()
                batch.clear()

        except Exception:
            # Mark any queued items as completed before propagating failure.
            for _ in batch:
                self.queue.task_done()
            raise

    def _write_batch(self, batch):
        trades = [item[0] for item in batch]
        self.ledger.record_trades(
            trades,
            batch[0][1],
        )
        self.ledger.commit()

    async def close(self):
        """Flush pending trades and stop the writer."""
        if self._closed:
            return

        self._closed = True

        if self.worker_task is not None:
            await self.worker_task
            await self.queue.join()

        self.ledger.close()
