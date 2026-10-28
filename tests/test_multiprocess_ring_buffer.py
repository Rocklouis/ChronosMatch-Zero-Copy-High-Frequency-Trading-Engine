
import multiprocessing as mp
import queue
import tempfile
import time
from pathlib import Path

from chronosmatch.order import Order, Side
from chronosmatch.ring_buffer import MmapRingBuffer

CAPACITY = 32
TOTAL_ORDERS = 500
TEST_TIMEOUT = 60


def producer(path, done, errors):
    """Write orders to the shared ring buffer."""
    try:
        with MmapRingBuffer.open_existing(path, CAPACITY) as buffer:
            for i in range(1, TOTAL_ORDERS + 1):
                order = Order(
                    order_id=i,
                    side=Side.BUY if i % 2 else Side.SELL,
                    price=50000 + i,
                    quantity=1,
                    timestamp=i,
                )

                while not buffer.push(order):
                    time.sleep(0.001)

    except Exception as exc:
        errors.put(f"Producer error: {type(exc).__name__}: {exc}")
    finally:
        done.set()


def consumer(path, done, results, errors):
    """Read orders and send their data to the parent process."""
    try:
        with MmapRingBuffer.open_existing(path, CAPACITY) as buffer:
            while not done.is_set() or not buffer.is_empty():
                order = buffer.pop()

                if order is None:
                    time.sleep(0.001)
                else:
                    results.put(
                        (order.order_id, order.price, order.quantity)
                    )

    except Exception as exc:
        errors.put(f"Consumer error: {type(exc).__name__}: {exc}")


def main():
    ctx = mp.get_context("spawn")

    with tempfile.TemporaryDirectory() as temp_dir:
        path = str(Path(temp_dir) / "shared_ring.dat")

        # Create and initialize the buffer once in the parent process.
        with MmapRingBuffer(path, CAPACITY):
            pass

        done = ctx.Event()
        results = ctx.Queue()
        errors = ctx.Queue()

        p_consumer = ctx.Process(
            target=consumer,
            args=(path, done, results, errors),
            name="ring-consumer",
        )
        p_producer = ctx.Process(
            target=producer,
            args=(path, done, errors),
            name="ring-producer",
        )

        received = []
        deadline = time.monotonic() + TEST_TIMEOUT

        try:
            p_consumer.start()
            p_producer.start()

            # Read results while workers are running.
            # This prevents a large result queue from blocking shutdown.
            while len(received) < TOTAL_ORDERS:
                remaining = deadline - time.monotonic()

                if remaining <= 0:
                    raise TimeoutError(
                        f"Timed out after receiving {len(received)} "
                        f"of {TOTAL_ORDERS} orders"
                    )

                try:
                    item = results.get(timeout=min(0.1, remaining))
                    received.append(item)
                except queue.Empty:
                    if not p_producer.is_alive():
                        # The producer has stopped. Allow the consumer
                        # time to finish delivering any remaining orders.
                        if not p_consumer.is_alive():
                            break

            # Give the consumer a chance to exit after draining the buffer.
            p_producer.join(timeout=2)
            p_consumer.join(timeout=5)

            if p_producer.is_alive():
                raise TimeoutError("Producer did not exit")

            if p_consumer.is_alive():
                raise TimeoutError("Consumer did not exit")

            # Retrieve any reported worker errors.
            messages = []
            while True:
                try:
                    messages.append(errors.get_nowait())
                except queue.Empty:
                    break

            if messages:
                raise RuntimeError("; ".join(messages))

            if p_producer.exitcode != 0 or p_consumer.exitcode != 0:
                raise RuntimeError(
                    f"Unexpected exit codes: "
                    f"producer={p_producer.exitcode}, "
                    f"consumer={p_consumer.exitcode}"
                )

            expected = [
                (i, 50000 + i, 1)
                for i in range(1, TOTAL_ORDERS + 1)
            ]

            if received != expected:
                raise AssertionError(
                    f"Data mismatch: expected {len(expected)} ordered "
                    f"records, received {len(received)}"
                )

            print(f"Producer wrote: {TOTAL_ORDERS}")
            print(f"Consumer received: {len(received)}")
            print("FIFO order and record integrity: PASS")
            print("Multiprocess ring-buffer test: PASS")

        finally:
            # Avoid leaving worker processes behind if the test fails.
            for process in (p_producer, p_consumer):
                if process.is_alive():
                    process.terminate()
                if process.pid is not None:
                    process.join(timeout=3)

            results.close()
            errors.close()
            results.join_thread()
            errors.join_thread()


if __name__ == "__main__":
    main()
