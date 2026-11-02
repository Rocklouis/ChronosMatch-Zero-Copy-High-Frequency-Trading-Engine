
import curses
import random
import time

from chronosmatch.matching_core import CythonMatchingCore


def draw_text(screen, y, x, text):
    height, width = screen.getmaxyx()
    if 0 <= y < height and x < width:
        screen.addnstr(y, x, str(text), max(0, width - x - 1))


def run_dashboard(screen):
    curses.curs_set(0)
    screen.nodelay(True)
    screen.timeout(100)

    engine = CythonMatchingCore()
    order_id = 0
    processed = 0
    last_update = time.perf_counter()

    while True:
        key = screen.getch()
        if key in (ord("q"), ord("Q")):
            break

        # Generate a simulated order for the demo.
        order_id += 1
        side = random.choice((0, 1))  # 0 = BUY, 1 = SELL

        if side == 0:
            price = random.randint(49_900, 50_010)
        else:
            price = random.randint(49_990, 50_100)

        quantity = random.randint(1, 20)
        timestamp = time.perf_counter_ns()

        engine.add_order(
            order_id, side, price, quantity, timestamp
        )
        processed += 1

        bid, ask = engine.best_prices()
        bids, asks = engine.book_snapshot()

        # Best bid first; best ask first.
        bids = sorted(bids, key=lambda o: (-o[1], o[3], o[0]))
        asks = sorted(asks, key=lambda o: (o[1], o[3], o[0]))

        screen.erase()
        draw_text(screen, 0, 2, "CHRONOSMATCH - LIVE ORDER BOOK")
        draw_text(screen, 1, 2, "Simulated market data | Press Q to quit")
        draw_text(screen, 3, 2, f"Orders processed: {processed}")
        draw_text(screen, 4, 2, f"Best bid: {bid if bid is not None else 'N/A'}")
        draw_text(screen, 5, 2, f"Best ask: {ask if ask is not None else 'N/A'}")

        if bid is not None and ask is not None:
            draw_text(screen, 6, 2, f"Spread: {ask - bid}")
        else:
            draw_text(screen, 6, 2, "Spread: N/A")

        draw_text(screen, 8, 2, "BIDS (highest price first)")
        draw_text(screen, 8, 38, "ASKS (lowest price first)")
        draw_text(screen, 9, 2, "Order ID       Price    Qty")
        draw_text(screen, 9, 38, "Order ID       Price    Qty")

        for i in range(8):
            y = 10 + i
            if i < len(bids):
                oid, price, qty, _ = bids[i]
                draw_text(screen, y, 2, f"{oid:<14} {price:<8} {qty}")
            if i < len(asks):
                oid, price, qty, _ = asks[i]
                draw_text(screen, y, 38, f"{oid:<14} {price:<8} {qty}")

        screen.refresh()

        # Keep the demo readable and limit its update rate.
        now = time.perf_counter()
        delay = 0.10 - (now - last_update)
        if delay > 0:
            time.sleep(delay)
        last_update = time.perf_counter()


if __name__ == "__main__":
    curses.wrapper(run_dashboard)
