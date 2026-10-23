
import asyncio
import tempfile
from pathlib import Path

from chronosmatch.firehose import MarketFirehose
from chronosmatch.order import Order, Side
from chronosmatch.ring_buffer import MmapRingBuffer
from matching_engine import MatchingEngine


async def main():
    total_orders = 10_000
    capacity = 256

    engine = MatchingEngine()
    orders_written = 0
    orders_processed = 0
    trade_count = 0

    with tempfile.TemporaryDirectory() as temp_dir:
        buffer_path = Path(temp_dir) / "chronosmatch_ring.bin"

        start = asyncio.get_running_loop().time()

        with MmapRingBuffer(buffer_path, capacity) as ring:
            firehose = MarketFirehose(target_rate=1_000_000)

            async for order in firehose.stream(total_orders):
                # Keep the demo single-process and sequential.
                # If the buffer is full, drain it before retrying.
                if not ring.push(order):
                    while True:
                        queued_order = ring.pop()
                        if queued_order is None:
                            break

                        trades = engine.add_order(queued_order)
                        orders_processed += 1
                        trade_count += len(trades)

                    if not ring.push(order):
                        raise RuntimeError("Buffer remained full after draining")

                orders_written += 1

                # Drain periodically to exercise the bounded ring.
                if len(ring) >= capacity // 2:
                    while True:
                        queued_order = ring.pop()
                        if queued_order is None:
                            break

                        trades = engine.add_order(queued_order)
                        orders_processed += 1
                        trade_count += len(trades)

            # Process any remaining queued orders.
            while True:
                queued_order = ring.pop()
                if queued_order is None:
                    break

                trades = engine.add_order(queued_order)
                orders_processed += 1
                trade_count += len(trades)

        elapsed = asyncio.get_running_loop().time() - start

    print("=== ChronosMatch End-to-End Test ===")
    print(f"Orders written:   {orders_written}")
    print(f"Orders processed: {orders_processed}")
    print(f"Trades generated: {trade_count}")
    print(f"Elapsed time:     {elapsed:.6f} seconds")

    if elapsed > 0:
        print(f"Throughput:       {orders_processed / elapsed:,.0f} orders/sec")

    assert orders_written == total_orders, "Not all orders were written"
    assert orders_processed == total_orders, "Not all orders were processed"
    assert orders_processed == orders_written, "Order count mismatch"

    print("End-to-end pipeline: PASS")


if __name__ == "__main__":
    asyncio.run(main())

