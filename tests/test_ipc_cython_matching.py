
import multiprocessing as mp
import queue
import tempfile
import time
from pathlib import Path

from chronosmatch.order import Order, Side
from chronosmatch.ring_buffer import MmapRingBuffer
from chronosmatch.matching_core import CythonMatchingCore


CAPACITY = 32
TEST_TIMEOUT = 30

# Deterministic orders for testing price-time matching.
TEST_ORDERS = [
    Order(1, Side.BUY, 100, 5, 1),
    Order(2, Side.SELL, 99, 3, 2),
    Order(3, Side.SELL, 101, 4, 3),
    Order(4, Side.BUY, 101, 2, 4),
]


def producer(path, done, errors):
    """Write test orders into the shared mmap ring buffer."""
    try:
        with MmapRingBuffer.open_existing(path, CAPACITY) as buffer:
            for order in TEST_ORDERS:
                while not buffer.push(order):
                    time.sleep(0.001)

    except Exception as exc:
        errors.put(f"Producer error: {type(exc).__name__}: {exc}")

    finally:
        done.set()


def consumer(path, done, results, errors):
    """Read mmap orders and process them using the Cython engine."""
    try:
        engine = CythonMatchingCore()
        processed = 0
        trades = []

        with MmapRingBuffer.open_existing(path, CAPACITY) as buffer:
            while not done.is_set() or not buffer.is_empty():
                order = buffer.pop()

                if order is None:
                    time.sleep(0.001)
                    continue

                order_trades = engine.add_order(
                    order.order_id,
                    int(order.side),
                    order.price,
                    order.quantity,
                    order.timestamp,
                )

                trades.extend(order_trades)
                processed += 1

        results.put((
            processed,
            trades,
            engine.book_snapshot(),
            engine.best_prices(),
        ))

    except Exception as exc:
        errors.put(f"Consumer error: {type(exc).__name__}: {exc}")


def test_mmap_ipc_with_cython_matching():
    ctx = mp.get_context("spawn")

    with tempfile.TemporaryDirectory() as temp_dir:
        path = str(Path(temp_dir) / "cython_matching_ring.dat")

        # Initialize the shared ring buffer before starting workers.
        with MmapRingBuffer(path, CAPACITY):
            pass

        done = ctx.Event()
        results = ctx.Queue()
        errors = ctx.Queue()

        p_consumer = ctx.Process(
            target=consumer,
            args=(path, done, results, errors),
        )

        p_producer = ctx.Process(
            target=producer,
            args=(path, done, errors),
        )

        try:
            p_consumer.start()
            p_producer.start()

            p_producer.join(TEST_TIMEOUT)
            p_consumer.join(TEST_TIMEOUT)

            if p_producer.is_alive() or p_consumer.is_alive():
                raise TimeoutError("IPC matching workers timed out")

            if p_producer.exitcode != 0:
                raise RuntimeError(
                    f"Producer exited with code {p_producer.exitcode}"
                )

            if p_consumer.exitcode != 0:
                raise RuntimeError(
                    f"Consumer exited with code {p_consumer.exitcode}"
                )

            messages = []
            while True:
                try:
                    messages.append(errors.get_nowait())
                except queue.Empty:
                    break

            if messages:
                raise RuntimeError("; ".join(messages))

            processed, trades, snapshot, best_prices = results.get(
                timeout=5
            )

            expected_trades = [
    (1, 2, 100, 3),
    (4, 3, 101, 2),
]

            expected_snapshot = (
                ((1, 100, 2, 1),),
                ((3, 101, 2, 3),),
            )

            assert processed == 4
            assert trades == expected_trades
            assert snapshot == expected_snapshot
            assert best_prices == (100, 101)

            print("Orders processed:", processed)
            print("Trades generated:", len(trades))
            print("Trades:", trades)
            print("Final book:", snapshot)
            print("Best bid/ask:", best_prices)
            print("mmap IPC + Cython matching: PASS")

        finally:
            for process in (p_producer, p_consumer):
                if process.is_alive():
                    process.terminate()
                if process.pid is not None:
                    process.join(timeout=3)

            results.close()
            errors.close()
