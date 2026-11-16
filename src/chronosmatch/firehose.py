
import asyncio
import time

from chronosmatch.order import Order, Side


class MarketFirehose:
    """Asynchronously generate mock market orders."""

    def __init__(self, target_rate: int = 100_000):
        if target_rate <= 0:
            raise ValueError("Target rate must be positive")

        self.target_rate = target_rate
        self.interval = 1.0 / target_rate
        self.order_id = 0

    async def stream(self, total_orders: int):
        """Yield mock orders at the configured target rate."""
        if total_orders < 0:
            raise ValueError("total_orders cannot be negative")

        next_time = time.perf_counter()

        for _ in range(total_orders):
            now = time.perf_counter()

            if now < next_time:
                await asyncio.sleep(next_time - now)

            self.order_id += 1

            order = Order(
                order_id=self.order_id,
                side=Side.BUY if self.order_id % 2 else Side.SELL,
                price=50_000 + (self.order_id % 100),
                quantity=1 + (self.order_id % 100),
                timestamp=time.perf_counter_ns(),
            )

            yield order
            next_time += self.interval

