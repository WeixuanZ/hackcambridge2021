from typing import Union, Dict, List

from optibook.common_types import PriceVolume as PriceVolumeTuple
from optibook.common_types import PriceBook
from optibook.synchronous_client import Exchange

# For order logging
g_recent_orders = [""] * 100


class Order:
    def __init__(self, instrument_id: str, price: float, volume: int, side: str, order_type: str):
        self.instrument_id = instrument_id
        self.price = price
        self.volume = volume
        self.side = side
        self.order_type = order_type


def get_spread(book: PriceBook) -> Union[float, None]:
    """ Get bid-ask spread
    """
    if book.asks and book.bids:
        return book.asks[0].price - book.bids[0].price
    else:
        return None


def get_best_price(book: PriceBook, side: str) -> PriceVolumeTuple:
    """ Returns the best (price, volume) object that we can buy/sell from the given book
    """
    # Order books are already sorted (best price first)
    # but make sure that they are not empty!
    if side == "buy" or side == "ask":
        if not book.asks:
            return PriceVolumeTuple(100000, 0)
        else:
            return book.asks[0]
    elif side == "sell" or side == "bid":
        if not book.bids:
            return PriceVolumeTuple(0, 0)
        else:
            return book.bids[0]
    else:
        raise Exception("best_price: side should be either 'buy' or 'sell'")


def make_orders(exchange: Exchange, orders: List[Order]):
    # Orders in form of [Order]
    order_results = list(map(
        lambda order: exchange.insert_order(order.instrument_id, price=order.price, volume=order.volume,
                                            side=order.side, order_type=order.order_type),
        orders
    ))

    for (order, order_id) in zip(orders, order_results):
        trade_history = exchange.get_trade_history(order.instrument_id)

        if len(trade_history) > 0 and trade_history[-1].order_id == order_id:
            success_msg = "SUCCESS"
        else:
            success_msg = "FAILED "

        order_log = f"Order: {order_id} {success_msg}     | Instrument: {order.instrument_id} | Price: {order.price:.1f} | Volume: {order.volume} | Side: {order.side} | Order Type: {order.order_type}"

        g_recent_orders.pop(0)
        g_recent_orders.append(order_log)
        print(order_log)


def log_recent_orders() -> None:
    for status in g_recent_orders:
        print(status)


def clear_all_positions(exchange: Exchange) -> None:
    """ Clear all positions without regard to loss
    """
    for s, p in exchange.get_positions().items():
        if p > 0:
            exchange.insert_order(s, price=1, volume=p, side='ask', order_type='ioc')
        elif p < 0:
            exchange.insert_order(s, price=100000, volume=-p, side='bid', order_type='ioc')


def sell_all_positions(exchange: Exchange, positions: Dict[str, int], max_a: PriceVolumeTuple, max_b: PriceVolumeTuple):
    """ Sell all positions at the highest price
    """

    print("SELLING")

    if max_a is None or max_b is None:
        return

    if max_a.price > max_b.price:
        maxPriceA = max_a.price
        maxVolA = max_a.volume #min(positions["PHILIPS_A"], max_a.volume)
        if maxVolA > 0:
            make_orders(exchange, [Order("PHILIPS_A", maxPriceA, maxVolA, "ask", "ioc")])
    else:
        maxPriceB = max_b.price
        maxVolB = max_b.volume #min(positions["PHILIPS_B"], max_b.volume)
        if maxVolB > 0:
            make_orders(exchange, [Order("PHILIPS_B", maxPriceB, maxVolB, "ask", "ioc")])


def buy_all_positions(exchange: Exchange, positions: Dict[str, int], min_a: PriceVolumeTuple, min_b: PriceVolumeTuple):
    """ Buy all positions at the lowest price
    """

    print("BUYING")

    if min_a is None or min_b is None:
        return

    if min_a.price < min_b.price:
        maxVolA = min_a.volume #min(positions["PHILIPS_A"], min_a.volume)
        if maxVolA > 0:
            make_orders(exchange, [Order("PHILIPS_A", min_a.price, maxVolA, "bid", "ioc")])
    else:
        maxVolB = min_b.volume # min(positions["PHILIPS_B"], min_b.volume)
        if maxVolB > 0:
            make_orders(exchange, [Order("PHILIPS_B", min_b.price, maxVolB, "bid", "ioc")])


def balance_individual(exchange, positions: Dict[str, int], instrument, target, individual_threshold):
    if positions[instrument] > individual_threshold:
        max_price = get_best_price(exchange.get_last_price_book(instrument), "sell")
        make_orders(exchange, [Order(instrument, max_price.price, 100, "ask", "ioc")])

    elif positions[instrument] < -individual_threshold:
        min_price = get_best_price(exchange.get_last_price_book(instrument), "buy")
        make_orders(exchange, [Order(instrument, min_price.price, 100, "bid", "ioc")])

    else:
        return False

    return True


def balance_positions(exchange: Exchange, total_threshold: int = 100, individual_threshold: int = 400):
    positions = exchange.get_positions()

    pos_a, pos_b = positions["PHILIPS_A"], positions["PHILIPS_B"]
    total_position = pos_a + pos_b

    if balance_individual(exchange, positions, "PHILIPS_A", 200, individual_threshold) or \
            balance_individual(exchange, positions, "PHILIPS_B", 200, individual_threshold):
        return True

    if total_position > total_threshold:
        sell_all_positions(
            exchange, positions,
            max_a=get_best_price(exchange.get_last_price_book("PHILIPS_A"), "sell"),
            max_b=get_best_price(exchange.get_last_price_book("PHILIPS_B"), "sell")
        )

    elif total_position < -total_threshold:
        buy_all_positions(
            exchange, positions,
            min_a=get_best_price(exchange.get_last_price_book("PHILIPS_A"), "buy"),
            min_b=get_best_price(exchange.get_last_price_book("PHILIPS_B"), "buy")
        )

    return False
