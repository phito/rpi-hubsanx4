from hubsan import Hubsan
from a7105_const import *
import a7105
import RPi.GPIO as GPIO
import logging
import time

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    a7105.init()
    logging.info('A7105 initialized.')
    quad = Hubsan()
    quad.bind()
    logging.info('Bound to Hubsanx4')
    quad.throttle = 0.5

    raw_input("Press Enter to continue...")
    quad.stop()
    GPIO.cleanup()
