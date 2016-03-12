from hubsan import Hubsan
from a7105_const import *
import a7105
import RPi.GPIO as GPIO
import logging
import time

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    a7105.init()
    a7105.setup()
    hubs = Hubsan(1)
    logging.info('A7105 initialized.')
    hubs.bind()
    hubs.safety()
    logging.info('Bound to Hubsanx4')
    while True:
        hubs.control(0xA0, 128, 128, 128, False)
        time.sleep(0.01)
    GPIO.cleanup()
