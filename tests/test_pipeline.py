
import asyncio
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from chronosmatch.firehose import MarketFirehose
from chronosmatch.ring_buffer import MmapRingBuffer


async def main():
    total_orders = 10_000
    received = 0

    with tempfile.TemporaryDirectory() as temp_dir:
        path = Path(temp_dir) / "pipeline.dat"

        with MmapRingBuffer(path, capacity=total_orders) as buffer:
            firehose = MarketFirehose(target_rate=100_000)

            async for order in firehose.stream(total_orders):
                if not buffer.push(order):
                    raise RuntimeError("Ring buffer unexpectedly full")

            while not buffer.is_empty():
                order = buffer.pop()

                if order is None:
                    raise RuntimeError("Unexpected empty buffer")

                order.validate()
                received += 1

    print(f"Orders generated: {total_orders}")
    print(f"Orders consumed: {received}")
    print("Pipeline test:", "PASS" if received == total_orders else "FAIL")


if __name__ == "__main__":
    asyncio.run(main())
