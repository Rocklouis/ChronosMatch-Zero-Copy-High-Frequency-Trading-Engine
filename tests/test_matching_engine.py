
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).parent / "src"))

from chronosmatch.order import Order, Side
from matching_engine import MatchingEngine


def make_order(order_id, side, price, quantity, timestamp):
    return Order(
        order_id=order_id,
        side=side,
        price=price,
        quantity=quantity,
        timestamp=timestamp,
    )


class TestMatchingEngine(unittest.TestCase):

    def setUp(self):
        self.engine = MatchingEngine()

    def test_unmatched_buy_stays_in_book(self):
        trades = self.engine.add_order(
            make_order(1, Side.BUY, 100, 10, 1)
        )
        self.assertEqual(trades, [])
        self.assertEqual(self.engine.best_bid(), 100)
        self.assertIsNone(self.engine.best_ask())

    def test_full_match(self):
        self.engine.add_order(make_order(1, Side.SELL, 100, 10, 1))
        trades = self.engine.add_order(
            make_order(2, Side.BUY, 100, 10, 2)
        )

        self.assertEqual(len(trades), 1)
        self.assertEqual(trades[0].price, 100)
        self.assertEqual(trades[0].quantity, 10)
        self.assertIsNone(self.engine.best_ask())

    def test_partial_match(self):
        self.engine.add_order(make_order(1, Side.SELL, 100, 10, 1))
        trades = self.engine.add_order(
            make_order(2, Side.BUY, 100, 4, 2)
        )

        self.assertEqual(trades[0].quantity, 4)
        self.assertEqual(self.engine.asks[0].quantity, 6)

    def test_price_priority(self):
        self.engine.add_order(make_order(1, Side.SELL, 105, 5, 1))
        self.engine.add_order(make_order(2, Side.SELL, 100, 5, 2))

        trades = self.engine.add_order(
            make_order(3, Side.BUY, 105, 5, 3)
        )

        self.assertEqual(trades[0].sell_order_id, 2)
        self.assertEqual(trades[0].price, 100)

    def test_time_priority_at_same_price(self):
        self.engine.add_order(make_order(1, Side.SELL, 100, 5, 1))
        self.engine.add_order(make_order(2, Side.SELL, 100, 5, 2))

        trades = self.engine.add_order(
            make_order(3, Side.BUY, 100, 5, 3)
        )

        self.assertEqual(trades[0].sell_order_id, 1)

    def test_unmatched_sell_stays_in_book(self):
        trades = self.engine.add_order(
            make_order(1, Side.SELL, 110, 7, 1)
        )
        self.assertEqual(trades, [])
        self.assertEqual(self.engine.best_ask(), 110)

    def test_sell_matches_best_bid(self):
        self.engine.add_order(make_order(1, Side.BUY, 105, 5, 1))
        self.engine.add_order(make_order(2, Side.BUY, 100, 5, 2))

        trades = self.engine.add_order(
            make_order(3, Side.SELL, 100, 5, 3)
        )

        self.assertEqual(trades[0].buy_order_id, 1)
        self.assertEqual(trades[0].price, 105)


if __name__ == "__main__":
    unittest.main(verbosity=2)

