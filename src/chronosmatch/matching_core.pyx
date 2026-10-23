
# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False
# cython: initializedcheck=False

from libc.stdint cimport int64_t


cdef struct BookOrder:
    int64_t order_id
    int64_t price
    int64_t quantity
    int64_t timestamp


cdef class CythonMatchingCore:
    cdef list bids
    cdef list asks

    def __cinit__(self):
        self.bids = []
        self.asks = []

    cpdef tuple best_prices(self):
        cdef object order
        cdef object bid_price = None
        cdef object ask_price = None

        for order in self.bids:
            if bid_price is None or order[1] > bid_price:
                bid_price = order[1]

        for order in self.asks:
            if ask_price is None or order[1] < ask_price:
                ask_price = order[1]

        return bid_price, ask_price

    cpdef int resting_order_count(self):
        return len(self.bids) + len(self.asks)
