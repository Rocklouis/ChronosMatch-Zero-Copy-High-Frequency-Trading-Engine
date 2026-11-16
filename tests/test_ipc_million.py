
import argparse
import multiprocessing as mp
import queue
import tempfile
import time
from pathlib import Path

from chronosmatch.order import Order, Side
from chronosmatch.ring_buffer import MmapRingBuffer


BATCH_SIZE = 256


def make_order(order_id):
    """Generate a reproducible order for integrity checks."""
    return Order(
        order_id=order_id,
        side=Side.BUY if order_id % 2 == 0 else Side.SELL,
        price=10000 + (order_id % 101),
        quantity=(order_id % 10) + 1,
        timestamp=order_id + 1,
    )


def verify_order(order, expected_id):
    expected = make_order(expected_id)
    return (
        order.order_id == expected.order_id
        and order.side == expected.side
        and order.price == expected.price
        and order.quantity == expected.quantity
        and order.timestamp == expected.timestamp
    )


def mmap_producer(path, capacity, count, status):
    """Produce orders in batches through the mmap ring buffer."""
    try:
        next_id = 1

        with MmapRingBuffer.open_existing(path, capacity) as ring:
            while next_id <= count:
                end_id = min(next_id + BATCH_SIZE, count + 1)
                batch = [
                    make_order(order_id)
                    for order_id in range(next_id, end_id)
                ]

                written = ring.push_many(batch)

                if written == 0:
                    time.sleep(0)
                else:
                    next_id += written

        status.put(("producer", "ok", count))

    except Exception as exc:
        status.put(("producer", "error", repr(exc)))


def mmap_consumer(path, capacity, count, status):
    """Consume batches and verify ordering and record contents."""
    try:
        received = 0
        checksum = 0

        with MmapRingBuffer.open_existing(path, capacity) as ring:
            while received < count:
                batch = ring.pop_many(BATCH_SIZE)

                if not batch:
                    time.sleep(0)
                    continue

                for order in batch:
                    expected_id = received + 1

                    if not verify_order(order, expected_id):
                        raise RuntimeError(
                            f"Corrupt or out-of-order record "
                            f"at {expected_id}"
                        )

                    received += 1
                    checksum += order.order_id

        status.put(("consumer", "ok", received, checksum))

    except Exception as exc:
        status.put(("consumer", "error", repr(exc)))


def pickle_producer(data_queue, count, status):
    """Send orders using multiprocessing.Queue and Pickle."""
    try:
        for order_id in range(1, count + 1):
            data_queue.put(make_order(order_id))

        status.put(("producer", "ok", count))

    except Exception as exc:
        status.put(("producer", "error", repr(exc)))


def pickle_consumer(data_queue, count, status):
    """Receive and verify orders sent through the Pickle queue."""
    try:
        received = 0
        checksum = 0

        while received < count:
            order = data_queue.get()

            expected_id = received + 1
            if not verify_order(order, expected_id):
                raise RuntimeError(
                    f"Corrupt or out-of-order record at {expected_id}"
                )

            received += 1
            checksum += order.order_id

        status.put(("consumer", "ok", received, checksum))

    except Exception as exc:
        status.put(("consumer", "error", repr(exc)))


def collect_results(processes, status, timeout=300):
    """Join workers, detect failures, and collect their status messages."""
    deadline = time.monotonic() + timeout

    for process in processes:
        remaining = max(0, deadline - time.monotonic())
        process.join(remaining)

    for process in processes:
        if process.is_alive():
            for worker in processes:
                if worker.is_alive():
                    worker.terminate()

            for worker in processes:
                worker.join()

            raise RuntimeError(
                "A worker timed out. Try a smaller test count first."
            )

    messages = []
    while True:
        try:
            messages.append(status.get_nowait())
        except queue.Empty:
            break

    failures = [
        message for message in messages
        if len(message) >= 2 and message[1] == "error"
    ]

    bad_exit = [
        process.exitcode for process in processes
        if process.exitcode != 0
    ]

    if failures or bad_exit or len(messages) != 2:
        raise RuntimeError(
            f"IPC test failed: messages={messages}, "
            f"exit_codes={bad_exit}"
        )

    status.close()
    status.join_thread()

    return messages


def run_mmap(ctx, root, count, capacity):
    path = str(root / "orders.mmap")

    # Initialize the shared file before starting the worker processes.
    with MmapRingBuffer(path, capacity):
        pass

    status = ctx.Queue()

    consumer = ctx.Process(
        target=mmap_consumer,
        args=(path, capacity, count, status),
    )
    producer = ctx.Process(
        target=mmap_producer,
        args=(path, capacity, count, status),
    )

    start = time.perf_counter()
    consumer.start()
    producer.start()

    results = collect_results([producer, consumer], status)
    elapsed = time.perf_counter() - start

    return elapsed, results


def run_pickle(ctx, count):
    """Run the separate Pickle-based multiprocessing baseline."""
    data_queue = ctx.Queue(maxsize=4096)
    status = ctx.Queue()

    consumer = ctx.Process(
        target=pickle_consumer,
        args=(data_queue, count, status),
    )
    producer = ctx.Process(
        target=pickle_producer,
        args=(data_queue, count, status),
    )

    start = time.perf_counter()
    consumer.start()
    producer.start()

    try:
        results = collect_results([producer, consumer], status)
        elapsed = time.perf_counter() - start
        return elapsed, results
    finally:
        data_queue.close()
        data_queue.join_thread()


def check_results(results, count):
    """Check worker statuses, received count, and order-ID checksum."""
    producer_results = [
        item for item in results
        if item[0] == "producer" and item[1] == "ok"
    ]
    consumer_results = [
        item for item in results
        if item[0] == "consumer" and item[1] == "ok"
    ]

    if len(producer_results) != 1 or len(consumer_results) != 1:
        raise RuntimeError(f"Missing worker result: {results}")

    if producer_results[0][2] != count:
        raise RuntimeError(f"Producer count mismatch: {results}")

    _, _, received, checksum = consumer_results[0]
    expected_checksum = count * (count + 1) // 2

    if received != count or checksum != expected_checksum:
        raise RuntimeError(
            f"Integrity check failed: received={received}, "
            f"checksum={checksum}, expected={expected_checksum}"
        )


def main():
    parser = argparse.ArgumentParser(
        description="Compare mmap ring-buffer IPC with a Pickle queue."
    )
    parser.add_argument("--count", type=int, default=1_000_000)
    parser.add_argument("--capacity", type=int, default=4096)
    args = parser.parse_args()

    if args.count <= 0 or args.capacity <= 0:
        parser.error("--count and --capacity must be positive")

    ctx = mp.get_context("spawn")

    print(f"Orders per test: {args.count:,}")
    print(f"mmap ring capacity: {args.capacity:,}")
    print(f"mmap batch size: {BATCH_SIZE}")
    print("Each test uses separate producer and consumer processes.")
    print()

    with tempfile.TemporaryDirectory(
        prefix="chronosmatch_ipc_"
    ) as temp:
        root = Path(temp)

        print("Running mmap IPC audit...")
        mmap_elapsed, mmap_results = run_mmap(
            ctx, root, args.count, args.capacity
        )
        check_results(mmap_results, args.count)

        print("Running Pickle queue baseline...")
        pickle_elapsed, pickle_results = run_pickle(
            ctx, args.count
        )
        check_results(pickle_results, args.count)

    mmap_rate = args.count / mmap_elapsed
    pickle_rate = args.count / pickle_elapsed

    print()
    print("=== IPC AUDIT RESULTS ===")
    print(f"mmap:   {mmap_elapsed:.3f} seconds")
    print(f"        {mmap_rate:,.0f} orders/second")
    print("        Integrity: PASS")
    print(f"Pickle: {pickle_elapsed:.3f} seconds")
    print(f"        {pickle_rate:,.0f} orders/second")
    print("        Integrity: PASS")

    ratio = pickle_elapsed / mmap_elapsed
    print(f"Elapsed-time ratio (Pickle/mmap): {ratio:.2f}x")
    print()
    print("Both tests passed record-count, ordering, and data checks.")
    print(
        "Timings include process startup and IPC overhead; "
        "they are not pure serialization or memory-copy timings."
    )


if __name__ == "__main__":
    mp.freeze_support()
    main()
