
import struct

from chronosmatch.order import Order, Side


# Fixed binary layout:
# order_id: unsigned 64-bit integer
# side:     unsigned 8-bit integer
# price:    unsigned 64-bit integer (paise)
# quantity: unsigned 64-bit integer
# timestamp: unsigned 64-bit integer
#
# "<" means little-endian, standard sizes, no alignment padding.
ORDER_STRUCT = struct.Struct("<QBQQQ")


def encode_order(order: Order) -> bytes:
    """Validate and encode an order into a fixed-size binary record."""
    order.validate()

    if order.order_id > 2**64 - 1:
        raise ValueError("Order ID exceeds binary format limit")
    if order.price > 2**64 - 1:
        raise ValueError("Price exceeds binary format limit")
    if order.quantity > 2**64 - 1:
        raise ValueError("Quantity exceeds binary format limit")
    if not 0 <= order.timestamp <= 2**64 - 1:
        raise ValueError("Timestamp exceeds binary format limit")

    return ORDER_STRUCT.pack(
        order.order_id,
        int(order.side),
        order.price,
        order.quantity,
        order.timestamp,
    )


def decode_order(data: bytes) -> Order:
    """Decode one fixed-size binary record into an Order."""
    if len(data) != ORDER_STRUCT.size:
        raise ValueError(
            f"Expected {ORDER_STRUCT.size} bytes, received {len(data)}"
        )

    order_id, side_value, price, quantity, timestamp = (
        ORDER_STRUCT.unpack(data)
    )

    try:
        side = Side(side_value)
    except ValueError as exc:
        raise ValueError(f"Invalid encoded order side: {side_value}") from exc

    order = Order(
        order_id=order_id,
        side=side,
        price=price,
        quantity=quantity,
        timestamp=timestamp,
    )
    order.validate()
    return order
