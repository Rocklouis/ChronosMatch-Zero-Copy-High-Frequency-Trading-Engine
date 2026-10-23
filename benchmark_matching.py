
import os
import sys
import time
import statistics

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from chronosmatch.matching_core import CythonMatchingCore
from chronosmatch.order import Order, Side
from matching_engine import MatchingEngine


def make_orders(count):
    """Create the same deterministic, non-crossing order stream."""
    orders = []

    for i in range(count):
        if i % 2 == 0:
            side = Side.BUY
            price = 100
        else:
            side = Side.SELL
            price = 110

        orders.append(
            Order(
                order_id=i + 1,
                side=side,
                price=price,
                quantity=1,
                timestamp=i + 1,
            )
        )

    return orders


def benchmark_python(orders):
    engine = MatchingEngine()
    start = time.perf_counter()

    for order in orders:
        engine.add_order(order)

    elapsed = time.perf_counter() - start
    return elapsed


def benchmark_cython(orders):
    engine = CythonMatchingCore()
    start = time.perf_counter()

    for order in orders:
        engine.add_order(
            order.order_id,
            int(order.side),
            order.price,
            order.quantity,
            order.timestamp,
        )

    elapsed = time.perf_counter() - start
    return elapsed


def main():
    count = 1000
    orders = make_orders(count)

    # Warm up the Cython extension before measurement.
    warmup = CythonMatchingCore()
    warmup.add_order(1, 0, 100, 1, 1)

    python_times = []
    cython_times = []

    for _ in range(3):
        python_times.append(benchmark_python(orders))
        cython_times.append(benchmark_cython(orders))

    python_avg = statistics.mean(python_times)
    cython_avg = statistics.mean(cython_times)

    print(f"Orders per run: {count}")
    print("Trials per implementation: 3")
    print(f"Python average: {python_avg:.6f} seconds")
    print(f"Cython average: {cython_avg:.6f} seconds")
    print(f"Python throughput: {count / python_avg:,.0f} orders/sec")
    print(f"Cython throughput: {count / cython_avg:,.0f} orders/sec")

    if cython_avg > 0:
        print(f"Measured speed ratio (Python/Cython): {python_avg / cython_avg:.2f}x")

    print("Note: preliminary benchmark; verify final book state and trade equivalence separately.")


if __name__ == "__main__":
    main()
