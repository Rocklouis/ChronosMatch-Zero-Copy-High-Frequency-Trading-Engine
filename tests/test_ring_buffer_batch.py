
import tempfile
from pathlib import Path

from chronosmatch.order import Order, Side
from chronosmatch.ring_buffer import MmapRingBuffer


def make_order(order_id, side=Side.BUY):
    return Order(
        order_id=order_id,
        side=side,
        price=50000 + order_id,
        quantity=10,
        timestamp=order_id * 100,
    )


def test_push_many_and_pop_many():
    with tempfile.TemporaryDirectory() as temp_dir:
        path = Path(temp_dir) / "ring.dat"

        with MmapRingBuffer(path, capacity=5) as buffer:
            orders = [
                make_order(1),
                make_order(2, Side.SELL),
                make_order(3),
                make_order(4, Side.SELL),
            ]

            assert buffer.push_many(orders) == 4
            assert len(buffer) == 4

            received = buffer.pop_many(3)
            assert received == orders[:3]
            assert len(buffer) == 1

            assert buffer.pop_many(5) == orders[3:]
            assert buffer.is_empty()

    print("PASS: Batch push and pop")


def test_push_many_respects_capacity():
    with tempfile.TemporaryDirectory() as temp_dir:
        path = Path(temp_dir) / "ring.dat"

        with MmapRingBuffer(path, capacity=2) as buffer:
            orders = [make_order(1), make_order(2), make_order(3)]

            assert buffer.push_many(orders) == 2
            assert buffer.pop_many(2) == orders[:2]
            assert buffer.is_empty()

    print("PASS: Batch capacity handling")


if __name__ == "__main__":
    test_push_many_and_pop_many()
    test_push_many_respects_capacity()
    print("All batch tests passed!")
