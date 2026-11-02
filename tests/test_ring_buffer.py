
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from chronosmatch.order import Order, Side
from chronosmatch.ring_buffer import MmapRingBuffer


def make_order(order_id: int, side: Side = Side.BUY) -> Order:
    """Create a valid test order."""
    return Order(
        order_id=order_id,
        side=side,
        price=50000 + order_id,
        quantity=10,
        timestamp=order_id * 100,
    )


def test_empty_buffer():
    """Verify that a new buffer is empty."""
    with tempfile.TemporaryDirectory() as temp_dir:
        path = Path(temp_dir) / "ring.dat"

        with MmapRingBuffer(path, capacity=3) as buffer:
            assert buffer.is_empty()
            assert len(buffer) == 0
            assert not buffer.is_full()
            assert buffer.pop() is None

    print("PASS: Empty buffer")


def test_full_buffer():
    """Verify that the buffer rejects orders when full."""
    with tempfile.TemporaryDirectory() as temp_dir:
        path = Path(temp_dir) / "ring.dat"

        with MmapRingBuffer(path, capacity=2) as buffer:
            assert buffer.push(make_order(1))
            assert buffer.push(make_order(2))

            assert buffer.is_full()
            assert len(buffer) == 2
            assert not buffer.push(make_order(3))
            assert len(buffer) == 2

    print("PASS: Full buffer")


def test_fifo_and_wraparound():
    """Verify FIFO order and reuse of slots after popping."""
    with tempfile.TemporaryDirectory() as temp_dir:
        path = Path(temp_dir) / "ring.dat"

        with MmapRingBuffer(path, capacity=3) as buffer:
            first = make_order(1)
            second = make_order(2, Side.SELL)
            third = make_order(3)
            fourth = make_order(4, Side.SELL)

            # Fill the buffer.
            assert buffer.push(first)
            assert buffer.push(second)
            assert buffer.push(third)
            assert buffer.is_full()

            # Remove one order and reuse its slot.
            assert buffer.pop() == first
            assert buffer.push(fourth)

            # Orders must still come out in FIFO order.
            assert buffer.pop() == second
            assert buffer.pop() == third
            assert buffer.pop() == fourth

            assert buffer.is_empty()
            assert len(buffer) == 0
            assert buffer.pop() is None

    print("PASS: FIFO order and wraparound")


def test_open_existing_buffer():
    """Verify that another buffer instance can attach to the same file."""
    with tempfile.TemporaryDirectory() as temp_dir:
        path = Path(temp_dir) / "ring.dat"
        expected = make_order(10, Side.SELL)

        with MmapRingBuffer(path, capacity=3) as writer:
            assert writer.push(expected)

            with MmapRingBuffer.open_existing(
                path, capacity=3
            ) as reader:
                assert reader.pop() == expected
                assert reader.is_empty()

    print("PASS: Open existing buffer")


if __name__ == "__main__":
    test_empty_buffer()
    test_full_buffer()
    test_fifo_and_wraparound()
    test_open_existing_buffer()
    print("All ring buffer tests passed!")
