
import statistics
import time

from chronosmatch.matching_core import CythonMatchingCore
from matching_engine import MatchingEngine
from chronosmatch.order import Order, Side


ORDERS_PER_TRIAL = 5000
TRIALS = 5


def make_orders(count):
    """Create a repeatable stream with crossing and resting orders."""
    orders = []

    for i in range(count):
        # Alternate buys and sells around a reference price.
        # Small price variations exercise multiple book levels.
        if i % 2 == 0:
            side = Side.BUY
            price = 10000 + (i % 10)
        else:
            side = Side.SELL
            price = 10000 + (i % 10)

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


def run_python(orders):
    engine = MatchingEngine()
    latencies_ns = []
    all_trades = []

    start_total = time.perf_counter_ns()

    for order in orders:
        start = time.perf_counter_ns()
        trades = engine.add_order(order)
        latencies_ns.append(time.perf_counter_ns() - start)
        all_trades.extend(trades)

    elapsed_ns = time.perf_counter_ns() - start_total

    return {
        "latencies_ns": latencies_ns,
        "elapsed_ns": elapsed_ns,
        "trades": all_trades,
        "book": (
    tuple(sorted(
        (o.order_id, o.price, o.quantity, o.timestamp)
        for o in engine.bids
    )),
    tuple(sorted(
        (o.order_id, o.price, o.quantity, o.timestamp)
        for o in engine.asks
    )),
),
    }


def run_cython(orders):
    engine = CythonMatchingCore()
    latencies_ns = []
    all_trades = []

    start_total = time.perf_counter_ns()

    for order in orders:
        start = time.perf_counter_ns()
        trades = engine.add_order(
            order.order_id,
            order.side.value,
            order.price,
            order.quantity,
            order.timestamp,
        )
        latencies_ns.append(time.perf_counter_ns() - start)
        all_trades.extend(trades)

    elapsed_ns = time.perf_counter_ns() - start_total

    return {
        "latencies_ns": latencies_ns,
        "elapsed_ns": elapsed_ns,
        "trades": all_trades,
        "book": engine.book_snapshot(),
    }


def percentile(values, percent):
    """Nearest-rank percentile."""
    ordered = sorted(values)
    index = max(0, (percent * len(ordered) + 99) // 100 - 1)
    return ordered[index]


def normalize_trades(trades):
    normalized = []

    for trade in trades:
        if isinstance(trade, (tuple, list)):
            normalized.append(tuple(trade))
        else:
            normalized.append((
                trade.buy_order_id,
                trade.sell_order_id,
                trade.price,
                trade.quantity,
            ))

    return normalized

def report(name, samples):
    latencies = samples["latencies_ns"]
    elapsed = samples["elapsed_ns"]
    count = len(latencies)

    print(f"\n{name}")
    print(f"  Orders:     {count:,}")
    print(f"  Total time: {elapsed / 1_000_000:.3f} ms")
    print(f"  Throughput: {count / (elapsed / 1_000_000_000):,.0f} orders/sec")
    print(f"  p50:        {percentile(latencies, 50):,} ns")
    print(f"  p95:        {percentile(latencies, 95):,} ns")
    print(f"  p99:        {percentile(latencies, 99):,} ns")
    print(f"  Maximum:    {max(latencies):,} ns")


def main():
    orders = make_orders(ORDERS_PER_TRIAL)

    # Verify behavior before collecting benchmark results.
    python_check = run_python(orders)
    cython_check = run_cython(orders)

    if normalize_trades(python_check["trades"]) != normalize_trades(
        cython_check["trades"]
    ):
        raise AssertionError("Python and Cython trades do not match")

    if python_check["book"] != cython_check["book"]:
        raise AssertionError("Python and Cython final books do not match")

    print("Correctness check: PASS")
    print(f"Orders per trial: {ORDERS_PER_TRIAL:,}")
    print("Trade results and final books match.")

    python_runs = []
    cython_runs = []

    for trial in range(1, TRIALS + 1):
        # Alternate order to reduce systematic warm-up bias.
        if trial % 2:
            python_runs.append(run_python(orders))
            cython_runs.append(run_cython(orders))
        else:
            cython_runs.append(run_cython(orders))
            python_runs.append(run_python(orders))

        print(f"Completed trial {trial}/{TRIALS}")

    # Report the middle trial's per-order distribution.
    # Also report aggregate throughput across all trials.
    python_samples = python_runs[len(python_runs) // 2]
    cython_samples = cython_runs[len(cython_runs) // 2]

    report("Python engine (middle trial latency distribution)", python_samples)
    report("Cython engine (middle trial latency distribution)", cython_samples)

    python_total_ns = sum(run["elapsed_ns"] for run in python_runs)
    cython_total_ns = sum(run["elapsed_ns"] for run in cython_runs)
    total_orders = ORDERS_PER_TRIAL * TRIALS

    print("\nAggregate throughput across all trials")
    print(
        f"  Python: {total_orders / (python_total_ns / 1_000_000_000):,.0f} orders/sec"
    )
    print(
        f"  Cython: {total_orders / (cython_total_ns / 1_000_000_000):,.0f} orders/sec"
    )

    if cython_total_ns > 0:
        print(
            "  Throughput ratio: "
            f"{python_total_ns / cython_total_ns:.2f}x"
        )

    print("\nNote: These are local benchmark results, not an HFT latency guarantee.")
    print("Per-order timings include Python call and timing overhead.")


if __name__ == "__main__":
    main()
