
from dataclasses import dataclass, replace

from chronosmatch.order import Order, Side


@dataclass(frozen=True, slots=True)
class Trade:
    buy_order_id: int
    sell_order_id: int
    price: int
    quantity: int


class MatchingEngine:
    """Simple Python limit order book with price-time priority."""

    def __init__(self):
        self.bids: list[Order] = []
        self.asks: list[Order] = []

    def add_order(self, order: Order) -> list[Trade]:
        """Accept an order, match it, and return completed trades."""
        order.validate()

        # Work on a copy so the caller's Order is not modified.
        incoming = replace(order)
        trades = []

        if incoming.side == Side.BUY:
            # Match against the lowest-priced eligible sell orders.
            while incoming.quantity > 0 and self.asks:
                best_ask = min(
                    self.asks,
                    key=lambda o: (o.price, o.timestamp, o.order_id),
                )

                if incoming.price < best_ask.price:
                    break

                quantity = min(incoming.quantity, best_ask.quantity)

                trades.append(
                    Trade(
                        buy_order_id=incoming.order_id,
                        sell_order_id=best_ask.order_id,
                        price=best_ask.price,
                        quantity=quantity,
                    )
                )

                incoming.quantity -= quantity
                best_ask.quantity -= quantity

                if best_ask.quantity == 0:
                    self.asks.remove(best_ask)

            if incoming.quantity > 0:
                self.bids.append(incoming)

        else:
            # Match against the highest-priced eligible buy orders.
            while incoming.quantity > 0 and self.bids:
                best_bid = max(
                    self.bids,
                    key=lambda o: (o.price, -o.timestamp, -o.order_id),
                )

                if incoming.price > best_bid.price:
                    break

                quantity = min(incoming.quantity, best_bid.quantity)

                trades.append(
                    Trade(
                        buy_order_id=best_bid.order_id,
                        sell_order_id=incoming.order_id,
                        price=best_bid.price,
                        quantity=quantity,
                    )
                )

                incoming.quantity -= quantity
                best_bid.quantity -= quantity

                if best_bid.quantity == 0:
                    self.bids.remove(best_bid)

            if incoming.quantity > 0:
                self.asks.append(incoming)

        return trades

    def best_bid(self) -> int | None:
        """Return the highest resting buy price, if one exists."""
        if not self.bids:
            return None
        return max(order.price for order in self.bids)

    def best_ask(self) -> int | None:
        """Return the lowest resting sell price, if one exists."""
        if not self.asks:
            return None
        return min(order.price for order in self.asks)
