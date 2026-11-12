
import argparse
import asyncio
import statistics
import time
from collections import deque

from rich import box
from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from chronosmatch.firehose import MarketFirehose
from chronosmatch.matching_core import CythonMatchingCore
from chronosmatch.async_ledger import AsyncTradeLedger
from chronosmatch.whale_detector import WhaleDetector


console = Console()


def format_price(price):
    if price is None:
        return "—"
    return f"{price:,}"


def build_dashboard(engine, recent_trades, whale_orders, latencies,
                    native_latencies, processed, elapsed, target_rate):

    bid, ask = engine.best_prices()

    spread = ask - bid if bid is not None and ask is not None else None

    # Order book
    bids, asks = engine.book_snapshot()

    book = Table(
        title="LIVE ORDER BOOK",
        box=box.ROUNDED,
        expand=True,
    )
    book.add_column("BUY ID", justify="right")
    book.add_column("BID PRICE", justify="right", style="green")
    book.add_column("BID QTY", justify="right")
    book.add_column("ASK PRICE", justify="right", style="red")
    book.add_column("ASK QTY", justify="right")
    book.add_column("SELL ID", justify="right")

    for i in range(5):
        bid_order = bids[-1 - i] if i < len(bids) else None
        ask_order = asks[-1 - i] if i < len(asks) else None

        book.add_row(
            str(bid_order[0]) if bid_order else "—",
            format_price(bid_order[1]) if bid_order else "—",
            str(bid_order[2]) if bid_order else "—",
            format_price(ask_order[1]) if ask_order else "—",
            str(ask_order[2]) if ask_order else "—",
            str(ask_order[0]) if ask_order else "—",
        )

    # Recent trades
    trades = Table(
        title="RECENT EXECUTED TRADES",
        box=box.ROUNDED,
        expand=True,
    )
    trades.add_column("BUY ID", justify="right")
    trades.add_column("SELL ID", justify="right")
    trades.add_column("PRICE", justify="right")
    trades.add_column("QUANTITY", justify="right")

    if recent_trades:
        for buy_id, sell_id, price, quantity in recent_trades:
            trades.add_row(
                str(buy_id),
                str(sell_id),
                format_price(price),
                str(quantity),
            )
    else:
        trades.add_row("—", "—", "No trades yet", "—")

    # Whale order alerts
    whales = Table(
        title="WHALE ORDER ALERTS",
        box=box.ROUNDED,
        expand=True,
    )
    whales.add_column("ORDER ID", justify="right")
    whales.add_column("SIDE", justify="center")
    whales.add_column("PRICE", justify="right")
    whales.add_column("QUANTITY", justify="right", style="bold yellow")
    whales.add_column("ALERT", justify="center", style="bold red")

    if whale_orders:
        for order_id, side, price, quantity in whale_orders:
            whales.add_row(
                str(order_id),
                side,
                format_price(price),
                str(quantity),
                "WHALE DETECTED",
            )
    else:
        whales.add_row("—", "—", "—", "—", "No whale orders yet")


    # Latency statistics
    latency_values = list(latencies)
    native_values = list(native_latencies)

    if native_values:
        native_ordered = sorted(native_values)
        native_p50 = statistics.median(native_ordered)
        native_p95 = native_ordered[
            min(int(len(native_ordered) * 0.95), len(native_ordered) - 1)
        ]
    else:
        native_p50 = native_p95 = 0

    if latency_values:
        ordered = sorted(latency_values)
        p50 = statistics.median(ordered)
        p95 = ordered[min(int(len(ordered) * 0.95), len(ordered) - 1)]
        maximum = max(ordered)
    else:
        p50 = p95 = maximum = 0

    throughput = processed / elapsed if elapsed > 0 else 0

    metrics = Table(box=box.SIMPLE, expand=True)
    metrics.add_column("METRIC", style="cyan")
    metrics.add_column("VALUE", justify="right")

    metrics.add_row("Orders processed", f"{processed:,}")
    metrics.add_row("Open orders", f"{engine.resting_order_count():,}")
    metrics.add_row("Best bid", format_price(bid))
    metrics.add_row("Best ask", format_price(ask))
    metrics.add_row("Spread", format_price(spread))
    metrics.add_row("Throughput", f"{throughput:,.0f} orders/sec")
    metrics.add_row("Latency p50", f"{p50:,.0f} ns")
    metrics.add_row("Latency p95", f"{p95:,.0f} ns")
    metrics.add_row("Latency max", f"{maximum:,.0f} ns")
    metrics.add_row("Native latency p50", f"{native_p50:,.0f} ns")
    metrics.add_row("Native latency p95", f"{native_p95:,.0f} ns")
    metrics.add_row(
    "Native matching loop (last)",
    f"{engine.last_match_duration_ns:,} ns"
)
    metrics.add_row("Target feed rate", f"{target_rate:,} orders/sec")

    header = Text(
        "CHRONOSMATCH | ZERO-COPY HIGH-FREQUENCY TRADING ENGINE",
        style="bold bright_cyan",
        justify="center",
    )

    status = Text(
        "SIMULATION FEED  |  CYTHON ENGINE ACTIVE  |  CTRL+C TO EXIT",
        style="bold green",
        justify="center",
    )

    return Group(
        Panel(header, border_style="cyan"),
        Panel(metrics, title="ENGINE METRICS", border_style="blue"),
        book,
        whales,
        trades,
        Panel(status, border_style="green"),
    )



async def run_dashboard(total_orders, target_rate):

    engine = CythonMatchingCore()
    firehose = MarketFirehose(target_rate=target_rate)
    whale_detector = WhaleDetector(threshold=90)
    whale_orders = deque(maxlen=8)

    ledger = AsyncTradeLedger(
        db_path="data/chronosmatch.db",
        batch_size=100,
        flush_interval=0.25,
    )

    recent_trades = deque(maxlen=8)
    latencies = deque(maxlen=2000)
    native_latencies = deque(maxlen=2000)

    processed = 0
    start_time = time.perf_counter()

    await ledger.start()

    try:
        with Live(
            console=console,
            refresh_per_second=8,
            screen=False,
        ) as live:

            async for order in firehose.stream(total_orders):
                if whale_detector.is_whale(order):
                    whale_orders.append(
                        (
                            order.order_id,
                            order.side.name,
                            order.price,
                            order.quantity,
                        )
                    )                
                start_ns = time.perf_counter_ns()

                trades = engine.add_order(
                    order.order_id,
                    int(order.side),
                    order.price,
                    order.quantity,
                    order.timestamp,
                )

                end_ns = time.perf_counter_ns()
                native_latencies.append(engine.last_match_duration_ns)

                latencies.append(end_ns - start_ns)

                for trade in trades:
                    recent_trades.append(trade)
                    await ledger.submit(trade)

                processed += 1

                if processed % 100 == 0 or processed == total_orders:
                    elapsed = time.perf_counter() - start_time

                    live.update(
                        build_dashboard(
                            engine,
                            recent_trades,
                            whale_orders,
                            latencies,
                            native_latencies,
                            processed,
                            elapsed,
                            target_rate,
                        )
                    )

                if processed % 100 == 0:
                    await asyncio.sleep(0)

    finally:
        await ledger.close()

    elapsed = time.perf_counter() - start_time

    console.print()
    console.print(
        f"[bold green]Completed:[/bold green] "
        f"{processed:,} orders in {elapsed:.3f} seconds"
    )



def main():
    parser = argparse.ArgumentParser(
        description="ChronosMatch live terminal dashboard"
    )

    parser.add_argument("--orders", type=int, default=10000)
    parser.add_argument("--rate", type=int, default=10000)

    args = parser.parse_args()

    if args.orders <= 0 or args.rate <= 0:
        parser.error("Orders and rate must be positive")

    try:
        asyncio.run(run_dashboard(args.orders, args.rate))
    except KeyboardInterrupt:
        console.print("\n[yellow]Dashboard stopped by user.[/yellow]")



def main():
    parser = argparse.ArgumentParser(
        description="ChronosMatch live terminal dashboard"
    )

    parser.add_argument("--orders", type=int, default=10000)
    parser.add_argument("--rate", type=int, default=10000)

    args = parser.parse_args()

    if args.orders <= 0 or args.rate <= 0:
        parser.error("Orders and rate must be positive")

    try:
        asyncio.run(run_dashboard(args.orders, args.rate))
    except KeyboardInterrupt:
        console.print("\n[yellow]Dashboard stopped by user.[/yellow]")



def main():
    parser = argparse.ArgumentParser(
        description="ChronosMatch live terminal dashboard"
    )

    parser.add_argument("--orders", type=int, default=10000)
    parser.add_argument("--rate", type=int, default=10000)

    args = parser.parse_args()

    if args.orders <= 0 or args.rate <= 0:
        parser.error("Orders and rate must be positive")

    try:
        asyncio.run(run_dashboard(args.orders, args.rate))
    except KeyboardInterrupt:
        console.print("\n[yellow]Dashboard stopped by user.[/yellow]")


if __name__ == "__main__":
    main()


