
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from chronosmatch.order import Order, Side
from chronosmatch.serialization import (
    ORDER_STRUCT,
    decode_order,
    encode_order,
)


def test_order_round_trip():
    original = Order(
        order_id=101,
        side=Side.BUY,
        price=50000,
        quantity=100,
        timestamp=123456789,
    )

    encoded = encode_order(original)
    decoded = decode_order(encoded)

    assert decoded == original
    assert len(encoded) == ORDER_STRUCT.size


if __name__ == "__main__":
    test_order_round_trip()
    print("Binary serialization test passed!")
    print(f"Encoded order size: {ORDER_STRUCT.size} bytes")
    print("Decoded order matches the original.")
