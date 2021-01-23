from utils import makeOrders, Order, get_spread, best_price


instrument_prefix = "PHILIPS_"
markets = ("A", "B")

# TODO: More limits/safeguards
MAX_TRADE_SIZE = 20


def sell_above(book, min_price: float) -> int:
    "Returns how much volume we can sell immediately to this order book above the minimum price given"
    return sum(bid.volume for bid in book.bids if bid.price > min_price)
    
    
def buy_below(book, max_price: float) -> int:
    "Returns how much volume we can buy immediately from this order book below the maximum price given"
    return sum(ask.volume for ask in book.asks if ask.price < max_price )
    

def try_arbitrage(books, one, two, e):
    "Tries to buy from one and sell to two. one and two can be 'A' or 'B'."
    assert one != two
    assert (one == "A") or (one == "B")
    assert (two == "A") or (two == "B")
    
    best_buy = best_price(books[one], "buy")
    volume = min(best_buy.volume, sell_above(books[two], best_buy.price + 0.05), MAX_TRADE_SIZE)
    
    if volume > 0:
        makeOrders([
            Order(instrument_prefix + one, best_buy.price, volume, "bid", "ioc"),
            Order(instrument_prefix + two, best_buy.price + 0.1, volume, "ask", "ioc")
        ], e)
        
        return True

    return False
    


def arbitrage(e):
    books = {market: e.get_last_price_book(instrument_prefix + market) for market in markets}
    
    try_arbitrage(books, "A", "B", e)
    try_arbitrage(books, "B", "A", e)
    
    
def stoikov_mm(e, instrument_id, volume=5, delta=0.1):
    e.delete_orders(instrument_id)
    book = e.get_last_price_book(instrument_id)
    
    spread = get_spread(book)
    if spread is not None and spread < 3*delta:
        return False
    
    best_ask = best_price(book, "ask")
    best_bid = best_price(book, "bid")
    
    makeOrders([
            Order(instrument_id, best_bid.price + delta, volume, "bid", "limit"),
            Order(instrument_id, best_ask.price - delta, volume, "ask", "limit")
        ], e)
        
    return True
