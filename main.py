from optibook.synchronous_client import Exchange
from strategy import arbitrage, stoikov_mm

import utils
import time

import logging


logger = logging.getLogger('client')
logger.setLevel('ERROR')

exchange = Exchange()
exchange.connect()

while True:
    arbitrage(exchange)
    utils.sellPosForHighest(exchange)
    stoikov_mm(exchange, "PHILIPS_A", volume=100)
    time.sleep(0.125)
