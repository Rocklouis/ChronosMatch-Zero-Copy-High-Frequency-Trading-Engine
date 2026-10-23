
import mmap
import struct
from pathlib import Path

from chronosmatch.order import Order, Side


# Header: read position and write position.
# Each position is an unsigned 64-bit integer.
HEADER = struct.Struct("<QQ")

# Each order occupies 33 bytes:
# order_id (8), side (1), price (8),
# quantity (8), timestamp (8).
ORDER_RECORD = struct.Struct("<QBQQQ")


class MmapRingBuffer:
    """Fixed-capacity FIFO ring buffer backed by a memory-mapped file.

    This initial version is intended for sequential access or use
    within one process. Concurrent processes need synchronization.
    Creating the buffer truncates and initializes the specified file.
    """

    def __init__(self, path: str | Path, capacity: int):
        if capacity <= 0:
            raise ValueError("Capacity must be positive")

        self.capacity = capacity
        self.path = Path(path)
        self._closed = False

        self._file = self.path.open("w+b")
        total_size = HEADER.size + capacity * ORDER_RECORD.size
        self._file.truncate(total_size)

        try:
            self._map = mmap.mmap(self._file.fileno(), 0)
            HEADER.pack_into(self._map, 0, 0, 0)
        except Exception:
            self._file.close()
            raise

    def _positions(self):
        return HEADER.unpack_from(self._map, 0)

    def __len__(self):
        head, tail = self._positions()
        return tail - head

    def is_empty(self):
        head, tail = self._positions()
        return head == tail

    def is_full(self):
        head, tail = self._positions()
        return tail - head >= self.capacity

    def push(self, order: Order) -> bool:
        """Write an order. Return False if the buffer is full."""
        order.validate()

        head, tail = self._positions()

        if tail - head >= self.capacity:
            return False

        offset = HEADER.size + (tail % self.capacity) * ORDER_RECORD.size

        ORDER_RECORD.pack_into(
            self._map,
            offset,
            order.order_id,
            int(order.side),
            order.price,
            order.quantity,
            order.timestamp,
        )

        # Publish the new write position after the record is written.
        HEADER.pack_into(self._map, 0, head, tail + 1)
        return True

    def pop(self) -> Order | None:
        """Read the oldest order, or return None if empty."""
        head, tail = self._positions()

        if head == tail:
            return None

        offset = HEADER.size + (head % self.capacity) * ORDER_RECORD.size

        order_id, side_value, price, quantity, timestamp = (
            ORDER_RECORD.unpack_from(self._map, offset)
        )

        try:
            side = Side(side_value)
        except ValueError as exc:
            raise ValueError(
                f"Invalid side value in buffer: {side_value}"
            ) from exc

        order = Order(
            order_id=order_id,
            side=side,
            price=price,
            quantity=quantity,
            timestamp=timestamp,
        )
        order.validate()

        # Release the slot only after reading the record.
        HEADER.pack_into(self._map, 0, head + 1, tail)
        return order

    def close(self):
        if not self._closed:
            self._map.close()
            self._file.close()
            self._closed = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
