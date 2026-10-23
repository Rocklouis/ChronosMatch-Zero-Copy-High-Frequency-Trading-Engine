
# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False

cdef class CythonMatchingCore:
    cdef list bids
    cdef list asks

    def __cinit__(self):
        self.bids = []
        self.asks = []

    cdef Py_ssize_t _best_index(self, list orders, bint is_bid):
        cdef Py_ssize_t i
        cdef Py_ssize_t best = 0
        cdef object current
        cdef object candidate

        for i in range(1, len(orders)):
            current = orders[best]
            candidate = orders[i]

            if is_bid:
                if candidate[1] > current[1]:
                    best = i
                elif candidate[1] == current[1]:
                    if candidate[3] < current[3]:
                        best = i
                    elif (
                        candidate[3] == current[3]
                        and candidate[0] < current[0]
                    ):
                        best = i
            else:
                if candidate[1] < current[1]:
                    best = i
                elif candidate[1] == current[1]:
                    if candidate[3] < current[3]:
                        best = i
                    elif (
                        candidate[3] == current[3]
                        and candidate[0] < current[0]
                    ):
                        best = i

        return best

    cpdef list add_order(
        self,
        long long order_id,
        int side,
        long long price,
        long long quantity,
        long long timestamp
    ):
        cdef list trades = []
        cdef list book
        cdef Py_ssize_t best
        cdef long long fill_qty
        cdef long long trade_price
        cdef object resting

        # Validate incoming order.
        if order_id < 0:
            raise ValueError("Invalid order ID")
        if side not in (0, 1):
            raise ValueError("Invalid order side")
        if price <= 0:
            raise ValueError("Price must be positive")
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        if timestamp < 0:
            raise ValueError("Timestamp cannot be negative")

        # Side 0 = BUY, side 1 = SELL.
        if side == 0:
            book = self.asks

            # Match incoming buy against the lowest eligible asks.
            while quantity > 0 and book:
                best = self._best_index(book, False)
                resting = book[best]

                if price < resting[1]:
                    break

                fill_qty = min(quantity, resting[2])
                trade_price = resting[1]

                trades.append((
                    order_id,
                    resting[0],
                    trade_price,
                    fill_qty
                ))

                quantity -= fill_qty
                resting[2] -= fill_qty

                if resting[2] == 0:
                    book.pop(best)

            # Store any unfilled buy quantity.
            if quantity > 0:
                self.bids.append(
                    [order_id, price, quantity, timestamp]
                )

        else:
            book = self.bids

            # Match incoming sell against the highest eligible bids.
            while quantity > 0 and book:
                best = self._best_index(book, True)
                resting = book[best]

                if price > resting[1]:
                    break

                fill_qty = min(quantity, resting[2])
                trade_price = resting[1]

                trades.append((
                    resting[0],
                    order_id,
                    trade_price,
                    fill_qty
                ))

                quantity -= fill_qty
                resting[2] -= fill_qty

                if resting[2] == 0:
                    book.pop(best)

            # Store any unfilled sell quantity.
            if quantity > 0:
                self.asks.append(
                    [order_id, price, quantity, timestamp]
                )

        return trades

    cpdef tuple best_prices(self):
        cdef object bid_price = None
        cdef object ask_price = None

        if self.bids:
            bid_price = self.bids[
                self._best_index(self.bids, True)
            ][1]

        if self.asks:
            ask_price = self.asks[
                self._best_index(self.asks, False)
            ][1]

        return bid_price, ask_price

    cpdef int resting_order_count(self):
        return len(self.bids) + len(self.asks)

    cpdef tuple book_snapshot(self):
        """Return immutable snapshots of resting bids and asks."""
        cdef list bids_snapshot = []
        cdef list asks_snapshot = []
        cdef object order

        for order in self.bids:
            bids_snapshot.append(tuple(order))

        for order in self.asks:
            asks_snapshot.append(tuple(order))

        return tuple(bids_snapshot), tuple(asks_snapshot)
