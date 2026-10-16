
import asyncio
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from chronosmatch.firehose import MarketFirehose
from chronosmatch.ring_buffer import MmapRingBuffer


async def run_trial(trial_number, total_orders=100_000):
    capacity = 1_024
    generated = 0
    consumed = 0
    producer_done = asyncio.Event()

    with tempfile.TemporaryDirectory() as temp_dir:
        path = Path(temp_dir) / "benchmark.dat"

        with MmapRingBuffer(path, capacity=capacity) as buffer:
            firehose = MarketFirehose(target_rate=10_000_000)

            async def producer():
                nonlocal generated
                try:
                    async for order in firehose.stream(total_orders):
                        while not buffer.push(order):
                            await asyncio.sleep(0)
                        generated += 1
                finally:
                    producer_done.set()

            async def consumer():
                nonlocal consumed
                while not producer_done.is_set() or not buffer.is_empty():
                    order = buffer.pop()
                    if order is None:
                        await asyncio.sleep(0)
                        continue

                    if order.order_id != consumed + 1:
                        raise AssertionError(
                            f"Out-of-order order: {order.order_id}"
                        )
                    consumed += 1

            start = time.perf_counter()
            await asyncio.gather(producer(), consumer())
            elapsed = time.perf_counter() - start

    if generated != total_orders or consumed != total_orders:
        raise AssertionError(
            f"Expected {total_orders}; generated {generated}, "
            f"consumed {consumed}"
        )

    throughput = consumed / elapsed
    print(
        f"Run {trial_number}: {consumed:,} orders in "
        f"{elapsed:.4f}s = {throughput:,.0f} orders/sec"
    )
    return throughput


async def main():
    results = []
    for trial in range(1, 4):
        results.append(await run_trial(trial))

    average = sum(results) / len(results)
    print(f"\nAverage throughput: {average:,.0f} orders/second")
    print("All benchmark trials passed.")


if __name__ == "__main__":
    asyncio.run(main())
