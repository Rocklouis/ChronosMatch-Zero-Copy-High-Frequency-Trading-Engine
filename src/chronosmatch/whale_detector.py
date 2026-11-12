
class WhaleDetector:
    """Detect unusually large orders using a configurable threshold."""

    def __init__(self, threshold=90):
        if threshold <= 0:
            raise ValueError("Whale threshold must be positive")

        self.threshold = threshold
        self.detected_orders = 0

    def is_whale(self, order):
        """Return True when an order meets the whale threshold."""
        if order.quantity >= self.threshold:
            self.detected_orders += 1
            return True

        return False

