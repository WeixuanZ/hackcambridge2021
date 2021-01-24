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

while not should_kill_attempt(exchange, START_PNL):
    time.sleep(0.125)
    
    print("tick")
    
    ma_A.update()

    if balance_positions(exchange):
        print("Balanced positions")
        continue # why continue though

    # arbitrage(exchange)
    stoikov_mm(exchange, "PHILIPS_A", ma_A.volatile(), delta=0, volume=5)

    if START_PNL is None:
        START_PNL = exchange.get_pnl()

print("Exit")
