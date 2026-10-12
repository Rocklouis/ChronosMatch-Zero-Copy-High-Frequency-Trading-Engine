from dataclasses import dataclass
from enum import IntEnum


class Side(IntEnum):
    BUY = 0
    SELL = 1


@dataclass(slots=True)
class Order:
    order_id: int
    side: Side
    price: int
    quantity: int
    timestamp: int

    def validate(self):
        if self.order_id < 0:
            raise ValueError("Invalid order ID")
        if self.side not in (Side.BUY, Side.SELL):
            raise ValueError("Invalid order side")
        if self.price <= 0:
            raise ValueError("Price must be positive")
        if self.quantity <= 0:
            raise ValueError("Quantity must be positive")