class MovingAverage:
    "Volume-weighed moving average"
    
    def __init__(self, exchange, instrument_id, length=50, threshold=0.1):
        self.e = exchange
        self.instrument_id = instrument_id
        self.length = length
        self.threshold = threshold
        self.series = []
        
        self.previous = 1000000
        self.volatility = 0
        
        
    def update(self):
        "Returns true if a sharp change has been detected"
        # IMPORTANT: Make sure no other functions use poll_new_trade_ticks!
        trades = self.e.poll_new_trade_ticks(self.instrument_id)
        
        if not trades:
            return
        
        for trade in trades:
            self.series.append(trade)
            if len(self.series) > self.length:
                self.series.pop(0)
        
        ma = sum(trade.price * trade.volume for trade in self.series) / sum(trade.volume for trade in self.series)
        
        self.volatility += max(abs(ma - self.previous) / self.previous, 0)
        
        self.previous = ma
        
    
    def volatile(self) -> bool:
        if self.volatility > self.threshold:
            print(f"VOLATILITY BREAKER HIT ({self.volatility})")
            self.volatility -= self.threshold
            return True
        
        return False
        