
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).parent / "src"))

from chronosmatch.order import Order, Side


def make_order(**overrides):
    values = {
        "order_id": 1,
        "side": Side.BUY,
        "price": 50000,
        "quantity": 100,
        "timestamp": 1,
    }
    values.update(overrides)
    return Order(**values)


class TestInvalidOrders(unittest.TestCase):

    def test_negative_order_id(self):
        with self.assertRaises(ValueError):
            make_order(order_id=-1).validate()

    def test_invalid_side(self):
        with self.assertRaises(ValueError):
            make_order(side=2).validate()

    def test_zero_price(self):
        with self.assertRaises(ValueError):
            make_order(price=0).validate()

    def test_negative_price(self):
        with self.assertRaises(ValueError):
            make_order(price=-100).validate()

    def test_zero_quantity(self):
        with self.assertRaises(ValueError):
            make_order(quantity=0).validate()

    def test_negative_quantity(self):
        with self.assertRaises(ValueError):
            make_order(quantity=-5).validate()


if __name__ == "__main__":
    unittest.main(verbosity=2)
