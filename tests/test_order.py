
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from chronosmatch.order import Order, Side


order = Order(
    order_id=1,
    side=Side.BUY,
    price=50000,  # ₹500.00 in paise
    quantity=100,
    timestamp=1,
)

order.validate()

print("Order validation successful!")
print(f"Order ID: {order.order_id}")
print(f"Side: {order.side.name}")
print(f"Price: ₹{order.price / 100:.2f}")
print(f"Quantity: {order.quantity}")
