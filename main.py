import time
import logging

from optibook.synchronous_client import Exchange

from strategy import should_kill_attempt, arbitrage, stoikov_mm
from utils import balance_positions
from moving_average import MovingAverage

logging.getLogger('client').setLevel('ERROR')

exchange = Exchange()
exchange.connect()

START_PNL = exchange.get_pnl()

ma_A = MovingAverage(exchange, "PHILIPS_A")

tick = 1

while not should_kill_attempt(exchange, START_PNL):
    time.sleep(0.11)
    
    print(f"tick {tick}")
    tick +=1
    
    ma_A.update()
    
    # Don't want to balance our trades from our MM positions
    exchange.delete_orders("PHILIPS_A")

    if balance_positions(exchange, total_threshold=40):
        print("Balanced positions")
        continue

    arbitrage(exchange)
    stoikov_mm(exchange, "PHILIPS_A", ma_A.volatile(), delta=0.1, volume=50)

    if START_PNL is None:
        START_PNL = exchange.get_pnl()

print("Exit")
