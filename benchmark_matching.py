
import statistics
import time

from chronosmatch.order import Order, Side
from chronosmatch.matching_core import CythonMatchingCore
from matching_engine import MatchingEngine


TRIALS = 3
ROUNDS = 200


def make_orders():
    orders = []
    order_id = 1

    # Create multiple bid levels and exercise partial fills.
    for level in range(ROUNDS):
        price = 100_000 + level * 10

        orders.append(
            Order(order_id, Side.BUY, price, 3, order_id)
        )
        order_id += 1

        orders.append(
            Order(order_id, Side.BUY, price - 1, 2, order_id)
        )
        order_id += 1

        orders.append(
            Order(order_id, Side.SELL, price - 1, 4, order_id)
        )
        order_id += 1

    # Add several ask levels, then sweep them with a marketable buy.
    for price, quantity in [
        (200_010, 2),
        (200_020, 3),
        (200_030, 4),
    ]:
        orders.append(
            Order(order_id, Side.SELL, price, quantity, order_id)
        )
        order_id += 1

    orders.append(
        Order(order_id, Side.BUY, 200_030, 6, order_id)
    )

    return orders


def normalize_trade(trade):
    if isinstance(trade, (tuple, list)):
        return tuple(trade)

    return (
        trade.buy_order_id,
        trade.sell_order_id,
        trade.price,
        getattr(trade, "quantity", getattr(trade, "fill_quantity", None)),
    )


def normalize_book_row(row):
    if isinstance(row, (tuple, list)):
        return tuple(row)

    return (
        row.order_id,
        row.price,
        getattr(row, "remaining_quantity", row.quantity),
        row.timestamp,
    )


def normalize_python_book(engine):
    bids = tuple(sorted(normalize_book_row(row) for row in engine.bids))
    asks = tuple(sorted(normalize_book_row(row) for row in engine.asks))
    return bids, asks


def run_python(orders):
    engine = MatchingEngine()
    all_trades = []

    start = time.perf_counter()

    for order in orders:
        trades = engine.add_order(order)
        all_trades.extend(normalize_trade(trade) for trade in trades)

    elapsed = time.perf_counter() - start
    return elapsed, tuple(all_trades), normalize_python_book(engine)


def run_cython(orders):
    engine = CythonMatchingCore()
    all_trades = []

    start = time.perf_counter()

    for order in orders:
        trades = engine.add_order(
            order.order_id,
            order.side.value,
            order.price,
            order.quantity,
            order.timestamp,
        )
        all_trades.extend(normalize_trade(trade) for trade in trades)

    elapsed = time.perf_counter() - start
    return elapsed, tuple(all_trades), engine.book_snapshot()


def main():
    orders = make_orders()

    # Verify correctness before timing results are accepted.
    python_result = run_python(orders)
    cython_result = run_cython(orders)

    if python_result[1] != cython_result[1]:
        raise AssertionError("Python and Cython trades differ!")

    if python_result[2] != cython_result[2]:
        raise AssertionError("Python and Cython order books differ!")

    print("Correctness check: PASS")
    print(f"Orders per run: {len(orders)}")
    print(f"Trades produced: {len(python_result[1])}")
    print("Final trade and book results match.")

    python_times = []
    cython_times = []

    # Each trial uses a fresh engine and the same order stream.
    for trial in range(1, TRIALS + 1):
        py_time, py_trades, py_book = run_python(orders)
        cy_time, cy_trades, cy_book = run_cython(orders)

        assert py_trades == cy_trades
        assert py_book == cy_book

        python_times.append(py_time)
        cython_times.append(cy_time)

        print(
            f"Trial {trial}: "
            f"Python={py_time:.6f}s, "
            f"Cython={cy_time:.6f}s"
        )

    py_avg = statistics.mean(python_times)
    cy_avg = statistics.mean(cython_times)

    print("\n--- Benchmark Summary ---")
    print(f"Python average: {py_avg:.6f} seconds")
    print(f"Cython average: {cy_avg:.6f} seconds")
    print(f"Python throughput: {len(orders) / py_avg:,.0f} orders/sec")
    print(f"Cython throughput: {len(orders) / cy_avg:,.0f} orders/sec")

    if cy_avg > 0:
        print(f"Measured speed ratio: {py_avg / cy_avg:.2f}x")

    print("All correctness checks passed.")
    print("Note: Results are local benchmark measurements, not an HFT latency guarantee.")


if __name__ == "__main__":
    main()
