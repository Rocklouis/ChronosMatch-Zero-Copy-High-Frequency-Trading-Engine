
import gc
import statistics
import time

from chronosmatch.matching_core import CythonMatchingCore

BOOK_SIZES = [100, 500, 1000, 2000, 5000]
TRIALS = 5
MATCHES_PER_TRIAL = 100


def run_trial(book_size):
    engine = CythonMatchingCore()

    # Insert the highest-priced BUY first.
    # This places the best bid at index 0.
    for i in range(book_size):
        engine.add_order(
            i + 1,
            0,                  # BUY
            200000 - i,
            10,
            i + 1
        )

    # Time repeated matches. Each match removes the first
    # resting order, requiring the remaining array to shift.
    start = time.perf_counter_ns()

    for j in range(MATCHES_PER_TRIAL):
        trades = engine.add_order(
            book_size + j + 1,
            1,                  # SELL
            1,                  # Crosses every resting BUY
            10,
            book_size + j + 1
        )

        if len(trades) != 1:
            raise RuntimeError(
                f"Expected 1 trade, received {len(trades)}"
            )

    elapsed_ns = time.perf_counter_ns() - start

    return elapsed_ns / MATCHES_PER_TRIAL


def main():
    print("ChronosMatch - Order Book Removal Scalability")
    print("=" * 60)
    print(f"Matches per trial: {MATCHES_PER_TRIAL}")
    print(f"Trials per book size: {TRIALS}")

    gc_was_enabled = gc.isenabled()
    gc.disable()

    try:
        for size in BOOK_SIZES:
            # Warm-up
            run_trial(size)

            results = [
                run_trial(size)
                for _ in range(TRIALS)
            ]

            median_ns = statistics.median(results)

            print(f"\nInitial resting orders: {size:,}")
            print(f"Median time per match: {median_ns:,.0f} ns")
            print(f"Median time per match: {median_ns / 1000:.2f} µs")

    finally:
        if gc_was_enabled:
            gc.enable()

    print("\nBenchmark completed.")


if __name__ == "__main__":
    main()
