
import unittest
from chronosmatch.matching_core import CythonMatchingCore


class TestCythonMatchingCore(unittest.TestCase):
    def setUp(self):
        self.book = CythonMatchingCore()

    def test_unmatched_buy(self):
        trades = self.book.add_order(1, 0, 100, 5, 1)

        self.assertEqual(trades, [])
        self.assertEqual(self.book.best_prices(), (100, None))
        self.assertEqual(self.book.resting_order_count(), 1)

    def test_full_match(self):
        self.book.add_order(1, 0, 100, 5, 1)
        trades = self.book.add_order(2, 1, 100, 5, 2)

        self.assertEqual(trades, [(1, 2, 100, 5)])
        self.assertEqual(self.book.best_prices(), (None, None))
        self.assertEqual(self.book.resting_order_count(), 0)

    def test_partial_match(self):
        self.book.add_order(1, 0, 100, 10, 1)
        trades = self.book.add_order(2, 1, 100, 4, 2)

        self.assertEqual(trades, [(1, 2, 100, 4)])
        self.assertEqual(self.book.best_prices(), (100, None))
        self.assertEqual(self.book.resting_order_count(), 1)

    def test_price_priority(self):
        self.book.add_order(1, 0, 100, 2, 1)
        self.book.add_order(2, 0, 105, 3, 2)

        trades = self.book.add_order(3, 1, 99, 3, 3)

        self.assertEqual(trades, [(2, 3, 105, 3)])
        self.assertEqual(self.book.best_prices(), (100, None))

    def test_time_priority(self):
        self.book.add_order(1, 0, 100, 2, 1)
        self.book.add_order(2, 0, 100, 2, 2)

        trades = self.book.add_order(3, 1, 100, 3, 3)

        self.assertEqual(
            trades,
            [(1, 3, 100, 2), (2, 3, 100, 1)]
        )

    def test_invalid_price(self):
        with self.assertRaises(ValueError):
            self.book.add_order(1, 0, 0, 5, 1)

    def test_unmatched_sell(self):
        trades = self.book.add_order(1, 1, 110, 4, 1)

        self.assertEqual(trades, [])
        self.assertEqual(self.book.best_prices(), (None, 110))
        self.assertEqual(self.book.resting_order_count(), 1)

    def test_sell_matches_best_bid(self):
        self.book.add_order(1, 0, 100, 3, 1)
        trades = self.book.add_order(2, 1, 95, 2, 2)

        self.assertEqual(trades, [(1, 2, 100, 2)])
        self.assertEqual(self.book.best_prices(), (100, None))

    def test_fill_across_multiple_price_levels(self):
        self.book.add_order(1, 0, 105, 2, 1)
        self.book.add_order(2, 0, 100, 3, 2)

        trades = self.book.add_order(3, 1, 99, 4, 3)

        self.assertEqual(
            trades,
            [(1, 3, 105, 2), (2, 3, 100, 2)]
        )
        self.assertEqual(self.book.best_prices(), (100, None))
        self.assertEqual(self.book.resting_order_count(), 1)
if __name__ == "__main__":
    unittest.main()
