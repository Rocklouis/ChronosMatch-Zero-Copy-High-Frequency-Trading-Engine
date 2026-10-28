
import mmap
import struct
from contextlib import nullcontext
from pathlib import Path

from filelock import FileLock
from chronosmatch.order import Order, Side

# Header: read position and write position (unsigned 64-bit integers).
HEADER = struct.Struct("<QQ")

# order_id, side, price, quantity, timestamp
ORDER_RECORD = struct.Struct("<QBQQQ")


class MmapRingBuffer:
    """File-backed FIFO ring buffer.

    Create the buffer with MmapRingBuffer(path, capacity).
    Attach to an existing buffer with open_existing(path, capacity).

    Locking is enabled by default for cross-process coordination.
    Set use_lock=False only when access is confined to one process
    with sequential operations.
    """

    def __init__(
        self,
        path: str | Path,
        capacity: int,
        use_lock: bool = True,
    ):
        if capacity <= 0:
            raise ValueError("Capacity must be positive")

        self.path = Path(path)
        self.capacity = capacity
        self._use_lock = use_lock
        self._closed = True

        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = FileLock(str(self.path) + ".lock")

        # Always protect initialization, even when use_lock=False.
        with self._lock:
            with self.path.open("x+b") as file:
                file.truncate(HEADER.size + capacity * ORDER_RECORD.size)
                file.flush()
                self._file = file

                try:
                    self._map = mmap.mmap(file.fileno(), 0)
                    HEADER.pack_into(self._map, 0, 0, 0)
                    self._map.flush()
                except Exception:
                    file.close()
                    self.path.unlink(missing_ok=True)
                    raise

        self._closed = False

    @classmethod
    def open_existing(
        cls,
        path: str | Path,
        capacity: int,
        use_lock: bool = True,
    ):
        """Attach to an existing buffer without truncating it."""
        if capacity <= 0:
            raise ValueError("Capacity must be positive")

        obj = cls.__new__(cls)
        obj.path = Path(path)
        obj.capacity = capacity
        obj._use_lock = use_lock
        obj._closed = True
        obj._lock = FileLock(str(obj.path) + ".lock")

        expected_size = HEADER.size + capacity * ORDER_RECORD.size

        # Always protect initialization and header validation.
        with obj._lock:
            obj._file = obj.path.open("r+b")

            try:
                if obj._file.seek(0, 2) != expected_size:
                    raise ValueError(
                        "File size does not match the requested capacity"
                    )

                obj._map = mmap.mmap(obj._file.fileno(), 0)
                head, tail = HEADER.unpack_from(obj._map, 0)

                if head > tail or tail - head > capacity:
                    raise ValueError("Invalid ring-buffer header")

            except Exception:
                if hasattr(obj, "_map"):
                    obj._map.close()
                obj._file.close()
                raise

        obj._closed = False
        return obj

    def _ensure_open(self):
        if self._closed:
            raise ValueError("Ring buffer is closed")

    def _guard(self):
        """Return a file lock or a no-op context manager."""
        if self._use_lock:
            return self._lock
        return nullcontext()

    def _positions(self):
        return HEADER.unpack_from(self._map, 0)

    def __len__(self):
        self._ensure_open()

        with self._guard():
            head, tail = self._positions()
            return tail - head

    def is_empty(self):
        self._ensure_open()

        with self._guard():
            head, tail = self._positions()
            return head == tail

    def is_full(self):
        self._ensure_open()

        with self._guard():
            head, tail = self._positions()
            return tail - head >= self.capacity

    def push(self, order: Order) -> bool:
        self._ensure_open()
        order.validate()

        with self._guard():
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

            # Publish the new tail after writing the record.
            HEADER.pack_into(self._map, 0, head, tail + 1)
            return True

    def pop(self) -> Order | None:
        self._ensure_open()

        with self._guard():
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

            HEADER.pack_into(self._map, 0, head + 1, tail)
            return order

    def push_many(self, orders) -> int:
        """Push as many orders as fit, using one lock acquisition."""
        self._ensure_open()
        batch = list(orders)

        # Validate orders before writing any records.
        for order in batch:
            order.validate()

        if not batch:
            return 0

        with self._guard():
            head, tail = self._positions()
            available = self.capacity - (tail - head)
            count = min(len(batch), available)

            for order in batch[:count]:
                offset = (
                    HEADER.size
                    + (tail % self.capacity) * ORDER_RECORD.size
                )

                ORDER_RECORD.pack_into(
                    self._map,
                    offset,
                    order.order_id,
                    int(order.side),
                    order.price,
                    order.quantity,
                    order.timestamp,
                )
                tail += 1

            # Publish all written records together.
            HEADER.pack_into(self._map, 0, head, tail)
            return count

    def pop_many(self, max_items: int) -> list[Order]:
        """Pop up to max_items orders, using one lock acquisition."""
        self._ensure_open()

        if max_items <= 0:
            raise ValueError("max_items must be positive")

        with self._guard():
            head, tail = self._positions()
            count = min(max_items, tail - head)
            orders = []

            for _ in range(count):
                offset = (
                    HEADER.size
                    + (head % self.capacity) * ORDER_RECORD.size
                )

                (
                    order_id,
                    side_value,
                    price,
                    quantity,
                    timestamp,
                ) = ORDER_RECORD.unpack_from(self._map, offset)

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
                orders.append(order)
                head += 1

            # Publish all consumed records together.
            HEADER.pack_into(self._map, 0, head, tail)
            return orders

    def close(self):
        if not self._closed:
            try:
                self._map.close()
            finally:
                self._file.close()
                self._closed = True

    def __enter__(self):
        self._ensure_open()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
