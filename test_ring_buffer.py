
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

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


def test_empty_buffer():
    with tempfile.TemporaryDirectory() as temp_dir:
        path = Path(temp_dir) / "ring.dat"
        with MmapRingBuffer(path, capacity=3) as buffer:
            assert buffer.is_empty()
            assert len(buffer) == 0
            assert buffer.pop() is None

    print("PASS: Empty buffer")


def test_full_buffer():
    with tempfile.TemporaryDirectory() as temp_dir:
        path = Path(temp_dir) / "ring.dat"
        with MmapRingBuffer(path, capacity=2) as buffer:
            assert buffer.push(make_order(1))
            assert buffer.push(make_order(2))
            assert buffer.is_full()
            assert not buffer.push(make_order(3))
            assert len(buffer) == 2

    print("PASS: Full buffer")


def test_fifo_and_wraparound():
    with tempfile.TemporaryDirectory() as temp_dir:
        path = Path(temp_dir) / "ring.dat"
        with MmapRingBuffer(path, capacity=3) as buffer:
            first = make_order(1)
            second = make_order(2, Side.SELL)
            third = make_order(3)
            fourth = make_order(4, Side.SELL)

            assert buffer.push(first)
            assert buffer.push(second)
            assert buffer.push(third)
            assert buffer.pop() == first
            assert buffer.push(fourth)

            assert buffer.pop() == second
            assert buffer.pop() == third
            assert buffer.pop() == fourth
            assert buffer.is_empty()
            assert buffer.pop() is None

    print("PASS: FIFO order and wraparound")


if __name__ == "__main__":
    test_empty_buffer()
    test_full_buffer()
    test_fifo_and_wraparound()
    print("All ring buffer tests passed!")
