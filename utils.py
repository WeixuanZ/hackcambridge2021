class Order:
    def __init__(self, instrument_id: str, price: float, volume: int, side: str, order_type: str):
        self.instrument_id = instrument_id
        self.price = price
        self.volume = volume
        self.side = side
        self.order_type = order_type


# TODO: Import this from optibook_client
class PriceVolume:
    """
    Bundles a price and a volume

    Attributes
    ----------
    price: float

    volume: int
    """
    def __init__(self, price, volume):
        self.price = price
        self.volume = volume


def get_spread(book) -> float:
    """Get bid-ask spread"""
    if book.asks and book.bids:
        return book.asks[0].price - book.bids[0].price
    else:
        return None

    
def best_price(book, side) -> float:
    "Returns the best (price, volume) object that we can buy/sell from the given book"
    # Order books are already sorted (best price first)
    # but make sure that they are not empty!
    if (side == "buy" or side == "ask"):
        if not book.asks:
            return PriceVolume(100000, 0)
        else:
            return book.asks[0]
    elif (side == "sell" or side == "bid"):
        if not book.bids:
            return PriceVolume(0, 0)
        else:
            return book.bids[0]
    else:
        raise Exception("best_price: side should be either 'buy' or 'sell'")

    

def clear():
    for s, p in exchange.get_positions().items():
        if p > 0:
            exchange.insert_order(s, price=1, volume=p, side='ask', order_type='ioc')
        elif p < 0:
            exchange.insert_order(s, price=100000, volume=-p, side='bid', order_type='ioc')
        


recentOrders = [""] * 100

def makeOrders(orders, exchange):
    # Orders in form of [Order]
    results = list(map(lambda order: exchange.insert_order(order.instrument_id, price=order.price, volume=order.volume, side=order.side, order_type=order.order_type), orders))
    for (i, result) in enumerate(results):
        tradeHistory = exchange.get_trade_history(orders[i].instrument_id)
        if (len(tradeHistory) > 0 and tradeHistory[-1].order_id == result):
            recentOrders.pop(0)
            recentOrders.append(f"Order: {result} SUCCESS     | Instrument: {orders[i].instrument_id} | Price: {orders[i].price:.1f} | Volume: {orders[i].volume} | Side: {orders[i].side} | Order Type: {orders[i].order_type}")
        else:
            recentOrders.pop(0)
            recentOrders.append(f"Order: {result} FAILED      | Instrument: {orders[i].instrument_id} | Price: {orders[i].price:.1f} | Volume: {orders[i].volume} | Side: {orders[i].side} | Order Type: {orders[i].order_type}")
        print(recentOrders[-1])
        
        
def printRecent():
    for status in recentOrders:
        print(status)

def sellPosForHighest(exchange):
    pos = exchange.get_positions()
    posA = pos["PHILIPS_A"]
    posB = pos["PHILIPS_B"]
    
    total_position = posA + posB
    
    if abs(total_position) < 200:
        return
    
    if total_position > 0:
        # We need to sell at the highest price
        maxA = best_price(exchange.get_last_price_book("PHILIPS_A"), "sell")
        maxB = best_price(exchange.get_last_price_book("PHILIPS_B"), "sell")
        if(maxA != None and maxB != None):
            if(maxA.price > maxB.price):
                maxPriceA = maxA.price
                maxVolA = min(posA, maxA.volume)
                if(maxVolA > 0):
                    makeOrders([Order("PHILIPS_A", maxPriceA, maxVolA, "ask", "ioc")], exchange)
            else:
                maxPriceB = maxB.price
                maxVolB = min(posB, maxB.volume)
                if(maxVolB > 0):
                    makeOrders([Order("PHILIPS_B", maxPriceB, maxVolB, "ask", "ioc")], exchange)
    elif total_position < 0:
        # We need to buy at the lowest price
        minA = best_price(exchange.get_last_price_book("PHILIPS_A"), "buy")
        minB = best_price(exchange.get_last_price_book("PHILIPS_B"), "buy")
        if(minA != None and minB != None):
            if(minA.price < minB.price):
                minPriceA = minA.price
                maxVolA = minA.volume
                if(maxVolA > 0):
                    makeOrders([Order("PHILIPS_A", minPriceA, maxVolA, "bid", "ioc")], exchange)
            else:
                minPriceB = minB.price
                maxVolB = minB.volume
                if(maxVolB > 0):
                    makeOrders([Order("PHILIPS_B", minPriceB, maxVolB, "bid", "ioc")], exchange)