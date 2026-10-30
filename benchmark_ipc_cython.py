
import multiprocessing as mp
import queue
import tempfile
import time
from pathlib import Path

from chronosmatch.order import Order, Side
from chronosmatch.ring_buffer import MmapRingBuffer
from chronosmatch.matching_core import CythonMatchingCore


# Benchmark configuration
TOTAL_ORDERS = 10_000
CAPACITY = 1024
TEST_TIMEOUT = 60


def producer(path, total_orders, done, stop, errors):
    """Generate orders and write them into the shared mmap ring buffer."""

    try:
        with MmapRingBuffer.open_existing(path, CAPACITY) as buffer:

            for i in range(total_orders):
                if stop.is_set():
                    break

                side = Side.BUY if i % 2 == 0 else Side.SELL

                # BUY at 100 and SELL at 99 create crossing orders.
                price = 100 if side == Side.BUY else 99

                order = Order(
                    order_id=i + 1,
                    side=side,
                    price=price,
                    quantity=1,
                    timestamp=i + 1,
                )

                while not buffer.push(order):
                    if stop.is_set():
                        break
                    time.sleep(0.0001)

                if stop.is_set():
                    break

    except Exception as exc:
        errors.put(("producer", repr(exc)))
        stop.set()

    finally:
        done.set()


def consumer(path, total_orders, done, stop, results, errors):
    """Read mmap orders and process them using the Cython engine."""

    try:
        engine = CythonMatchingCore()

        processed = 0
        trade_count = 0

        with MmapRingBuffer.open_existing(path, CAPACITY) as buffer:

            # Process exactly the number of orders expected.
            while processed < total_orders:

                order = buffer.pop()

                if order is None:

                    # Producer has finished, but some orders are missing.
                    if done.is_set():
                        raise RuntimeError(
                            f"Producer finished after only "
                            f"{processed} of {total_orders} orders"
                        )

                    time.sleep(0.0001)
                    continue

                trades = engine.add_order(
                    order.order_id,
                    int(order.side),
                    order.price,
                    order.quantity,
                    order.timestamp,
                )

                processed += 1
                trade_count += len(trades)

        results.put({
            "processed": processed,
            "trades": trade_count,
            "book": engine.book_snapshot(),
            "best_prices": engine.best_prices(),
        })

    except Exception as exc:
        errors.put(("consumer", repr(exc)))
        stop.set()


def main():
    context = mp.get_context("spawn")

    with tempfile.TemporaryDirectory() as temp_dir:

        path = str(Path(temp_dir) / "benchmark_ipc.dat")

        done = context.Event()
        stop = context.Event()

        results = context.Queue()
        errors = context.Queue()

        # Initialize the shared mmap ring buffer.
        with MmapRingBuffer(path, CAPACITY):
            pass

        consumer_process = context.Process(
            target=consumer,
            args=(path, TOTAL_ORDERS, done, stop, results, errors),
        )

        producer_process = context.Process(
            target=producer,
            args=(path, TOTAL_ORDERS, done, stop, errors),
        )

        start_time = None

        try:
            print("Starting IPC + Cython benchmark...")

            consumer_process.start()

            start_time = time.perf_counter()

            producer_process.start()

            producer_process.join(TEST_TIMEOUT)

            if producer_process.is_alive():
                stop.set()
                raise TimeoutError("Producer process timed out")

            consumer_process.join(TEST_TIMEOUT)

            if consumer_process.is_alive():
                stop.set()
                raise TimeoutError("Consumer process timed out")

            elapsed = time.perf_counter() - start_time

            # Collect worker errors.
            worker_errors = []

            while True:
                try:
                    worker_errors.append(errors.get(timeout=0.5))
                except queue.Empty:
                    break

            if worker_errors:
                raise RuntimeError(f"Worker errors: {worker_errors}")

            if producer_process.exitcode != 0:
                raise RuntimeError(
                    f"Producer exited with code {producer_process.exitcode}"
                )

            if consumer_process.exitcode != 0:
                raise RuntimeError(
                    f"Consumer exited with code {consumer_process.exitcode}"
                )

            try:
                result = results.get(timeout=5)
            except queue.Empty:
                raise RuntimeError(
                    "Consumer did not return benchmark results"
                )

            processed = result["processed"]
            trades = result["trades"]

            throughput = processed / elapsed if elapsed > 0 else 0

            print("\n========== IPC + CYTHON BENCHMARK ==========")

            print(f"Orders generated : {TOTAL_ORDERS:,}")
            print(f"Orders processed : {processed:,}")
            print(f"Trades generated : {trades:,}")
            print(f"Elapsed time     : {elapsed:.6f} seconds")
            print(f"Throughput       : {throughput:,.0f} orders/second")

            print(f"Best bid/ask     : {result['best_prices']}")
            print(f"Final book       : {result['book']}")

            # Correctness checks.
            expected_trades = TOTAL_ORDERS // 2

            if processed != TOTAL_ORDERS:
                raise AssertionError(
                    f"Expected {TOTAL_ORDERS} orders, got {processed}"
                )

            if trades != expected_trades:
                raise AssertionError(
                    f"Expected {expected_trades} trades, got {trades}"
                )

            if result["best_prices"] != (None, None):
                raise AssertionError("Expected an empty order book")

            print("\nCorrectness check: PASS")
            print("IPC + Cython benchmark: PASS")

        finally:
            stop.set()

            for process in (producer_process, consumer_process):

                if process.pid is not None and process.is_alive():
                    process.terminate()

                if process.pid is not None:
                    process.join(timeout=3)

            results.close()
            errors.close()


if __name__ == "__main__":
    mp.freeze_support()
    main()
