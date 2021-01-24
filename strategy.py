from utils import make_orders, Order, get_spread, get_best_price

instrument_prefix = "PHILIPS_"
markets = ("A", "B")

MAX_TRADE_SIZE = 20
MAX_LOSS_AMOUNT = 1000


def sell_above(book, min_price: float) -> int:
    """Returns how much volume we can sell immediately to this order book above the minimum price given"""
    return sum(bid.volume for bid in book.bids if bid.price > min_price)


def buy_below(book, max_price: float) -> int:
    """Returns how much volume we can buy immediately from this order book below the maximum price given"""
    return sum(ask.volume for ask in book.asks if ask.price < max_price)


def try_arbitrage(e, books, one, two):
    """Tries to buy from one and sell to two. one and two can be 'A' or 'B'."""
    assert one != two
    assert (one == "A") or (one == "B")
    assert (two == "A") or (two == "B")

    best_buy = get_best_price(books[one], "buy")
    volume = min(best_buy.volume, sell_above(books[two], best_buy.price + 0.05), MAX_TRADE_SIZE)

    if volume > 0:
        make_orders(e, [
            Order(instrument_prefix + one, best_buy.price, volume, "bid", "ioc"),
            Order(instrument_prefix + two, best_buy.price + 0.1, volume, "ask", "ioc")
        ])

        return True

    return False


def arbitrage(e):
    books = {market: e.get_last_price_book(instrument_prefix + market) for market in markets}

    try_arbitrage(e, books, "A", "B")
    try_arbitrage(e, books, "B", "A")


def stoikov_mm(e, instrument_id, volatile, volume=5, delta=0):
    e.delete_orders(instrument_id)
    
    # Stay out of the markets until they calm down
    if volatile:
        return
    
    book = e.get_last_price_book(instrument_id)

    spread = get_spread(book)
    if spread is None or spread < 0.5 or spread < 5 * delta:
        print("Spread is too tight")
        return False
        
    if spread > 1:
        delta = 0.1
        volumn = 20

    best_ask = get_best_price(book, "ask")
    best_bid = get_best_price(book, "bid")

    make_orders(e, [
        Order(instrument_id, best_bid.price + delta, volume, "bid", "limit"),
        Order(instrument_id, best_ask.price - delta, volume, "ask", "limit")
    ])

    return True


def should_kill_attempt(exchange, start_pnl):
    current_pnl = exchange.get_pnl()

    if current_pnl is None or start_pnl is None:
        print("get_pnl failed")
        return False

    if current_pnl < start_pnl - MAX_LOSS_AMOUNT:
        print(f"Starting pnl {start_pnl}")
        print(f"Current pnl {current_pnl}")
        return True

    return False
