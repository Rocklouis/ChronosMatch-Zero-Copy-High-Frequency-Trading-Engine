
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from chronosmatch.order import Order, Side
from chronosmatch.matching_core import CythonMatchingCore
from matching_engine import MatchingEngine


def normalize_trades(trades):
    result = []

    for trade in trades:
        if isinstance(trade, tuple):
            result.append(tuple(trade))
        else:
            result.append((
                trade.buy_order_id,
                trade.sell_order_id,
                trade.price,
                trade.quantity,
            ))

    return result


def normalize_python_book(orders, is_bid):
    rows = [
        (o.order_id, o.price, o.quantity, o.timestamp)
        for o in orders
    ]

    if is_bid:
        rows.sort(key=lambda x: (-x[1], x[3], x[0]))
    else:
        rows.sort(key=lambda x: (x[1], x[3], x[0]))

    return tuple(rows)


def normalize_cython_book(rows, is_bid):
    rows = list(rows)

    if is_bid:
        rows.sort(key=lambda x: (-x[1], x[3], x[0]))
    else:
        rows.sort(key=lambda x: (x[1], x[3], x[0]))

    return tuple(rows)


class TestEngineEquivalence(unittest.TestCase):
    def test_trades_and_final_book_match(self):
        python_engine = MatchingEngine()
        cython_engine = CythonMatchingCore()

        orders = [
            Order(1, Side.BUY, 100, 5, 1),
            Order(2, Side.BUY, 105, 3, 2),
            Order(3, Side.SELL, 99, 4, 3),
            Order(4, Side.SELL, 110, 2, 4),
            Order(5, Side.BUY, 115, 3, 5),
        ]

        for order in orders:
            python_trades = python_engine.add_order(order)

            cython_trades = cython_engine.add_order(
                order.order_id,
                int(order.side),
                order.price,
                order.quantity,
                order.timestamp,
            )

            self.assertEqual(
                normalize_trades(python_trades),
                normalize_trades(cython_trades),
            )

        python_book = (
            normalize_python_book(python_engine.bids, True),
            normalize_python_book(python_engine.asks, False),
        )

        cython_bids, cython_asks = cython_engine.book_snapshot()

        cython_book = (
            normalize_cython_book(cython_bids, True),
            normalize_cython_book(cython_asks, False),
        )

        self.assertEqual(python_book, cython_book)

    def test_equal_timestamp_uses_order_id_priority(self):
        engine = CythonMatchingCore()

        engine.add_order(20, 0, 100, 2, 5)
        engine.add_order(10, 0, 100, 2, 5)

        trades = engine.add_order(30, 1, 100, 3, 6)

        self.assertEqual(
            trades,
            [(10, 30, 100, 2), (20, 30, 100, 1)]
        )

    def test_partial_fill_across_multiple_levels(self):
        engine = CythonMatchingCore()

        engine.add_order(1, 0, 105, 2, 1)
        engine.add_order(2, 0, 100, 3, 2)

        trades = engine.add_order(3, 1, 99, 4, 3)

        self.assertEqual(
            trades,
            [(1, 3, 105, 2), (2, 3, 100, 2)]
        )

        self.assertEqual(
            engine.book_snapshot(),
            (((2, 100, 1, 2),), ())
        )

    def test_non_crossing_order_remains_in_book(self):
        engine = CythonMatchingCore()

        engine.add_order(1, 0, 100, 5, 1)
        trades = engine.add_order(2, 1, 105, 3, 2)

        self.assertEqual(trades, [])

        self.assertEqual(
            engine.book_snapshot(),
            (((1, 100, 5, 1),), ((2, 105, 3, 2),))
        )
if __name__ == "__main__":
    unittest.main(verbosity=2)
