
import asyncio
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from chronosmatch.firehose import MarketFirehose
from chronosmatch.ring_buffer import MmapRingBuffer


async def main():
    total_orders = 10_000
    buffer_capacity = 1_024

    generated = 0
    consumed = 0
    producer_done = asyncio.Event()

    with tempfile.TemporaryDirectory() as temp_dir:
        path = Path(temp_dir) / "live_pipeline.dat"

        with MmapRingBuffer(path, capacity=buffer_capacity) as buffer:
            firehose = MarketFirehose(target_rate=100_000)

            async def producer():
                nonlocal generated

                try:
                    async for order in firehose.stream(total_orders):
                        # Wait for space if the ring buffer is full.
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

                    order.validate()

                    expected_id = consumed + 1
                    if order.order_id != expected_id:
                        raise AssertionError(
                            f"Expected order {expected_id}, "
                            f"received {order.order_id}"
                        )

                    consumed += 1

            start = time.perf_counter()

            await asyncio.gather(producer(), consumer())

            elapsed = time.perf_counter() - start

    print(f"Orders generated: {generated}")
    print(f"Orders consumed: {consumed}")
    print(f"Elapsed time: {elapsed:.4f} seconds")
    print(f"Throughput: {consumed / elapsed:,.0f} orders/second")
    print(
        "Pipeline test:",
        "PASS" if generated == total_orders and consumed == total_orders
        else "FAIL",
    )

    assert generated == total_orders
    assert consumed == total_orders


if __name__ == "__main__":
    asyncio.run(main())
