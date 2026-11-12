
import asyncio

from chronosmatch.async_ledger import AsyncTradeLedger


async def main():
    ledger = AsyncTradeLedger(
        db_path=":memory:",
        batch_size=2,
        flush_interval=0.1,
    )

    await ledger.start()

    await ledger.submit((1001, 1002, 50000, 25))
    await ledger.submit((1003, 1004, 50010, 10))
    await ledger.submit((1005, 1006, 50020, 15))

    await ledger.close()

    print("Async ledger test completed successfully.")


if __name__ == "__main__":
    asyncio.run(main())
