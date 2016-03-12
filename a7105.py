from config import *
from a7105_const import *
import spidev
import RPi.GPIO as GPIO
import time

spi = spidev.SpiDev()

def set_register(address, value):
    GPIO.output(PIN_SCS, False)
    spi.xfer([address, value])
    GPIO.output(PIN_SCS, True)

def get_register(address):
    GPIO.output(PIN_SCS, False)
    spi.xfer([0x40 | address])
    result = spi.readbytes(1)[0]
    GPIO.output(PIN_SCS, True)
    return result

def init():
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(PIN_SCS, GPIO.OUT)
    # initializing SPI
    spi.open(0, 0)
    spi.lsbfirst = False
    spi.mode = 0b00

    # set GIO in SDO, signal not inverted and output enabled
    set_register(Registers.GPIO1, 0b011001)

def write_data(data):
    # reset write pointer
    strobe(State.RST_WRPTR)
    GPIO.output(PIN_SCS, False)
    # write to fifo register
    spi.xfer([Registers.FIFO_DATA])
    spi.xfer(data)
    GPIO.output(PIN_SCS, True)

def read_data(len):
    # reset read pointer
    strobe(State.RST_RDPTR)
    GPIO.output(PIN_SCS, False)
    spi.xfer([0x40 | Registers.FIFO_DATA])
    data = spi.readbytes(len)
    GPIO.output(PIN_SCS, True)
    return data

def write_id(id):
    GPIO.output(PIN_SCS, False)
    spi.xfer([Registers.ID_DATA,
              (id >> 24) & 0xFF,
              (id >> 16) & 0xFF,
              (id >> 8) & 0xFF,
              (id) & 0xFF])
    GPIO.output(PIN_SCS, True)

def strobe(state):
    GPIO.output(PIN_SCS, False)
    spi.xfer([state])
    GPIO.output(PIN_SCS, True)

def set_power(power):
    pac, tbg = power_enums[power]
    set_register(Registers.TX_TEST, (pac << 3) | tbg)

def set_channel(channel):
    set_register(Registers.PLL1, channel)

def __clock():
    return int(time.time() * 1000)

def calibrate():
    # IF filter bank calibration
    __calibrate_if()
    __calibrate_vco(0x0)
    __calibrate_vco(0xA0)

def __calibrate_if():
    set_register(Registers.CALC, 0b1)
    ms = __clock()

    # 500ms timeout
    while __clock() - ms < 500:
        if get_register(Registers.CALC) == 0:
            break

    if __clock() - ms >= 500:
        raise Exception('IF calibration timed out')

    result = get_register(Registers.IF1)
    get_register(Registers.VCO)

    # returns true if the calibration is successful
    if (result & (1 << 4)) != 0:
        raise Exception('IF calibration failed')

def __calibrate_vco(channel):
    # VCO current calibration
    set_register(Registers.PLL1, channel)
    set_register(Registers.CALC, 2)
    ms = __clock()

    # 500ms timeout
    while __clock() - ms < 500:
        if get_register(Registers.CALC) == 0:
            break

    if __clock() - ms >= 500:
        raise Exception('VCO calibration timed out')

    result = get_register(Registers.VCO1)
    # calibration failed
    if (result & (1 << 3)) != 0:
        raise Exception('VCO calibration failed')
