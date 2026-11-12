
from chronosmatch.order import Order, Side
from chronosmatch.whale_detector import WhaleDetector


def make_order(quantity, order_id=1):
    return Order(
        order_id=order_id,
        side=Side.BUY,
        price=50000,
        quantity=quantity,
        timestamp=123456789,
    )


def test_below_threshold_is_not_whale():
    detector = WhaleDetector(threshold=90)

    assert detector.is_whale(make_order(89)) is False
    assert detector.detected_orders == 0


def test_at_threshold_is_whale():
    detector = WhaleDetector(threshold=90)

    assert detector.is_whale(make_order(90)) is True
    assert detector.detected_orders == 1


def test_above_threshold_is_whale():
    detector = WhaleDetector(threshold=90)

    assert detector.is_whale(make_order(100)) is True
    assert detector.detected_orders == 1
