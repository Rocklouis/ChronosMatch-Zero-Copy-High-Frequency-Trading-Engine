
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from chronosmatch.firehose import MarketFirehose


async def main():
    firehose = MarketFirehose(target_rate=100_000)
    count = 0
    start = asyncio.get_running_loop().time()

    async for order in firehose.stream(10_000):
        if count == 0:
            print("First order:", order)
        count += 1

    elapsed = asyncio.get_running_loop().time() - start

    print(f"Orders generated: {count}")
    print(f"Elapsed time: {elapsed:.4f} seconds")
    print(f"Actual rate: {count / elapsed:,.0f} orders/second")


if __name__ == "__main__":
    asyncio.run(main())
