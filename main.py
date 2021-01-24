import time
import logging

from optibook.synchronous_client import Exchange

from strategy import should_kill_attempt, arbitrage, stoikov_mm
from utils import balance_positions

logging.getLogger('client').setLevel('ERROR')

exchange = Exchange()
exchange.connect()

START_PNL = exchange.get_pnl()

while not should_kill_attempt(exchange, START_PNL):
    time.sleep(0.125)

    if balance_positions(exchange):
        continue

    arbitrage(exchange)
    stoikov_mm(exchange, "PHILIPS_A", volume=5)

    if START_PNL is None:
        START_PNL = exchange.get_pnl()

print("Exit")
