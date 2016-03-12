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

def setup():
    strobe(State.STANDBY)
    __setup_registers()
    __calibrate()
    set_power(Power._30mW)
    strobe(State.STANDBY)

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

def __calibrate():
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

def __setup_registers():
    # auto RSSI measurement, auto IF Offset, FIFO mode enabled
    set_register(Registers.MODE_CTL, 0b01100011)
    # set FIFO length to 16 bytes (0x0f + 1)
    set_register(Registers.FIFO1, 0b1111);
    # use crystal oscillator, CLK divider = /2.
    set_register(Registers.CLOCK, 0b0101);

    # sanity check
    if get_register(Registers.CLOCK) != 0x05:
      raise Exception('Sanity check failed. Check wiring.')

    # set data rate to 25kbps.
    set_register(Registers.DATA_RATE, 0b0100);
    # frequency deviation: 186KHz
    set_register(Registers.TX2, 0b00101011);
    # BPF bandwidth = 500 KHz.
    set_register(Registers.RX, 0b01100010);
    # manual VGA, Mixer Gain: 24dB, LNA gain: 24dB.
    set_register(Registers.RX_GAIN1, 0b10000000);
    # set some reserved constants
    set_register(Registers.RX_GAIN4, 0b1010);
    # select ID code length of 4, preamble length of 4
    set_register(Registers.CODE1, 0b0111);
    # set demodulator DC estimation average mode,
    # ID code error tolerance = 1 bit, 16 bit preamble pattern detection length
    set_register(Registers.CODE2, 0b00010111);
    # set constants
    set_register(Registers.RX_TEST1, 0b01000111);
