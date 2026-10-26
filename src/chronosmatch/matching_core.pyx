
# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False
# cython: initializedcheck=False

from libc.stdlib cimport malloc, realloc, free
from libc.stddef cimport size_t
from time import perf_counter_ns

cdef struct COrder:
    long long order_id
    int side
    long long price
    long long quantity
    long long timestamp


cdef struct CTrade:
    long long buy_order_id
    long long sell_order_id
    long long price
    long long quantity


cdef Py_ssize_t best_index(
    COrder* orders,
    Py_ssize_t count,
    bint is_bid
) noexcept nogil:
    cdef Py_ssize_t i
    cdef Py_ssize_t best = 0

    for i in range(1, count):
        if is_bid:
            if orders[i].price > orders[best].price:
                best = i
            elif orders[i].price == orders[best].price:
                if orders[i].timestamp < orders[best].timestamp:
                    best = i
                elif orders[i].timestamp == orders[best].timestamp:
                    if orders[i].order_id < orders[best].order_id:
                        best = i
        else:
            if orders[i].price < orders[best].price:
                best = i
            elif orders[i].price == orders[best].price:
                if orders[i].timestamp < orders[best].timestamp:
                    best = i
                elif orders[i].timestamp == orders[best].timestamp:
                    if orders[i].order_id < orders[best].order_id:
                        best = i

    return best


cdef class CythonMatchingCore:
    cdef COrder* bids
    cdef COrder* asks
    cdef Py_ssize_t bid_count
    cdef Py_ssize_t ask_count
    cdef Py_ssize_t bid_capacity
    cdef Py_ssize_t ask_capacity
    cdef long long _last_match_duration_ns

    def __cinit__(self):
        self.bids = NULL
        self.asks = NULL
        self.bid_count = 0
        self.ask_count = 0
        self.bid_capacity = 0
        self.ask_capacity = 0
        self._last_match_duration_ns = 0

    def __dealloc__(self):
        if self.bids != NULL:
            free(self.bids)
        if self.asks != NULL:
            free(self.asks)

    cdef void _reserve_bids(self, Py_ssize_t needed) except *:
        cdef Py_ssize_t new_capacity
        cdef COrder* new_data

        if needed <= self.bid_capacity:
            return

        new_capacity = 16 if self.bid_capacity == 0 else self.bid_capacity
        while new_capacity < needed:
            new_capacity *= 2

        new_data = <COrder*>realloc(
            self.bids, <size_t>new_capacity * sizeof(COrder)
        )
        if new_data == NULL:
            raise MemoryError()

        self.bids = new_data
        self.bid_capacity = new_capacity

    cdef void _reserve_asks(self, Py_ssize_t needed) except *:
        cdef Py_ssize_t new_capacity
        cdef COrder* new_data

        if needed <= self.ask_capacity:
            return

        new_capacity = 16 if self.ask_capacity == 0 else self.ask_capacity
        while new_capacity < needed:
            new_capacity *= 2

        new_data = <COrder*>realloc(
            self.asks, <size_t>new_capacity * sizeof(COrder)
        )
        if new_data == NULL:
            raise MemoryError()

        self.asks = new_data
        self.ask_capacity = new_capacity

    cpdef list add_order(
        self,
        long long order_id,
        int side,
        long long price,
        long long quantity,
        long long timestamp
    ):
        cdef COrder incoming
        cdef COrder* opposite
        cdef Py_ssize_t rest_count
        cdef Py_ssize_t original_opposite_count
        cdef Py_ssize_t best
        cdef Py_ssize_t i
        cdef Py_ssize_t trade_count = 0
        cdef CTrade* trade_data = NULL
        cdef long long fill_qty
        cdef list trades = []
        cdef long long start_ns
        cdef long long end_ns

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

        incoming.order_id = order_id
        incoming.side = side
        incoming.price = price
        incoming.quantity = quantity
        incoming.timestamp = timestamp

        # Reserve capacity before entering native matching code.
        if side == 0:
            self._reserve_bids(self.bid_count + 1)
            opposite = self.asks
            rest_count = self.ask_count
        else:
            self._reserve_asks(self.ask_count + 1)
            opposite = self.bids
            rest_count = self.bid_count

        original_opposite_count = rest_count

        if rest_count > 0:
            trade_data = <CTrade*>malloc(
                <size_t>rest_count * sizeof(CTrade)
            )
            if trade_data == NULL:
                raise MemoryError()

        
        try:
            # Start timing immediately before native matching.
            start_ns = perf_counter_ns()

            # The matching loop uses only C-level values and arrays.
            with nogil:
                while incoming.quantity > 0 and rest_count > 0:
                    best = best_index(
                        opposite, rest_count, side == 1
                    )

            if side == 0:
                        if incoming.price < opposite[best].price:
                            break
                    else:
                        if incoming.price > opposite[best].price:
                            break

                    fill_qty = incoming.quantity
                    if opposite[best].quantity < fill_qty:
                        fill_qty = opposite[best].quantity

                    trade_data[trade_count].price = opposite[best].price
                    trade_data[trade_count].quantity = fill_qty

            if side == 0:
                        trade_data[trade_count].buy_order_id = incoming.order_id
                        trade_data[trade_count].sell_order_id = opposite[best].order_id
                    else:
                        trade_data[trade_count].buy_order_id = opposite[best].order_id
                        trade_data[trade_count].sell_order_id = incoming.order_id

                    trade_count += 1
                    incoming.quantity -= fill_qty
                    opposite[best].quantity -= fill_qty

                    if opposite[best].quantity == 0:
                        for i in range(best, rest_count - 1):
                            opposite[i] = opposite[i + 1]
                        rest_count -= 1

            # Stop timing immediately after native matching.
            end_ns = perf_counter_ns()
            self._last_match_duration_ns = end_ns - start_ns

            # Python-side book updates and result conversion follow.

            if side == 0:
                        if incoming.price < opposite[best].price:
                            break
                    else:
                        if incoming.price > opposite[best].price:
                            break

                    fill_qty = incoming.quantity
                    if opposite[best].quantity < fill_qty:
                        fill_qty = opposite[best].quantity

                    trade_data[trade_count].price = opposite[best].price
                    trade_data[trade_count].quantity = fill_qty

            if side == 0:
                        trade_data[trade_count].buy_order_id = incoming.order_id
                        trade_data[trade_count].sell_order_id = opposite[best].order_id
                    else:
                        trade_data[trade_count].buy_order_id = opposite[best].order_id
                        trade_data[trade_count].sell_order_id = incoming.order_id

                    trade_count += 1
                    incoming.quantity -= fill_qty
                    opposite[best].quantity -= fill_qty

                    if opposite[best].quantity == 0:
                        for i in range(best, rest_count - 1):
                            opposite[i] = opposite[i + 1]
                        rest_count -= 1

            if side == 0:
                self.ask_count = rest_count
                if incoming.quantity > 0:
                    self.bids[self.bid_count] = incoming
                    self.bid_count += 1
            else:
                self.bid_count = rest_count
                if incoming.quantity > 0:
                    self.asks[self.ask_count] = incoming
                    self.ask_count += 1

            for i in range(trade_count):
                trades.append((
                    trade_data[i].buy_order_id,
                    trade_data[i].sell_order_id,
                    trade_data[i].price,
                    trade_data[i].quantity
                ))

            return trades
        finally:
            if trade_data != NULL:
                free(trade_data)

    cpdef tuple best_prices(self):
        cdef object bid_price = None
        cdef object ask_price = None
        cdef Py_ssize_t idx

        if self.bid_count > 0:
            idx = best_index(self.bids, self.bid_count, True)
            bid_price = self.bids[idx].price

        if self.ask_count > 0:
            idx = best_index(self.asks, self.ask_count, False)
            ask_price = self.asks[idx].price

        return bid_price, ask_price

    cpdef int resting_order_count(self):
        return <int>(self.bid_count + self.ask_count)
        cpdef long long get_last_match_duration_ns(self):
        return self._last_match_duration_ns

    cpdef tuple book_snapshot(self):
        cdef list bids_snapshot = []
        cdef list asks_snapshot = []
        cdef Py_ssize_t i

        for i in range(self.bid_count):
            bids_snapshot.append((
                self.bids[i].order_id,
                self.bids[i].price,
                self.bids[i].quantity,
                self.bids[i].timestamp
            ))

        for i in range(self.ask_count):
            asks_snapshot.append((
                self.asks[i].order_id,
                self.asks[i].price,
                self.asks[i].quantity,
                self.asks[i].timestamp
            ))

        return tuple(bids_snapshot), tuple(asks_snapshot)
