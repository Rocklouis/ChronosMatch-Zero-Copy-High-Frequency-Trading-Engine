
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

    # Wait until all queued trades have been written.
    await ledger.queue.join()

    # Verify the actual SQLite records.
    stored = ledger.ledger.count_trades()
    print("Expected trades: 3")
    print("Stored trades:", stored)

    print("Recent trades:")
    for trade in ledger.ledger.get_recent_trades(3):
        print(trade)

    await ledger.close()

    assert stored == 3, "Trade storage verification failed!"

    print("ASYNC LEDGER VERIFICATION: PASS")


if __name__ == "__main__":
    asyncio.run(main())
