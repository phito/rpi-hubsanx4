from a7105_const import *
import a7105
import random
import logging
import time
import math
import threading

""" Hubsan x4 cyclic redundancy check """
def crc(packet):
    sum = 0
    for b in packet:
        sum += b
    return (256 - (sum % 256)) & 0xff

""" linear interpolation """
def lerp(t, min, max):
    return int(round(min + t * (max - min)))

def clamp(n, smallest, largest):
    return max(smallest, min(n, largest))

class Hubsan:
    # the Hubsan X4 can operate on the following 12 A7015 channels
    CHANNELS = [ 0x14, 0x1e, 0x28, 0x32, 0x3c, 0x46, 0x50, 0x5a, 0x64, 0x6e, 0x78, 0x82 ]

    def __init__(self):
        self.__thread = None
        self.__running = False
        self.throttle = 0
        self.yaw = 0.5
        self.pitch = 0.5
        self.roll = 0.5
        self.leds = True
        self.flips = False
        self.__setup_a7105()

    """ looks for an available quadcopter and binds with it """
    def bind(self):
        # generates a random 4bytes session id
        self.session_id = random.randint(0, 2147483647)
        # selects a random channel
        self.channel, = random.sample(Hubsan.CHANNELS, 1)

        a7105.write_id(0x55201041)
        a7105.set_channel(self.channel)

        # HANDSAKE 1
        logging.debug('binding sequence started on channel ' + str(self.channel))
        logging.debug('starting handshake 1')
        logging.debug('broadcasting discovery packet #1')
        stage = 1
        hubsan_id = 0

        while True:
            resp = self.__discovery(stage)
            if resp:
                stage = resp[0]
                logging.debug('received discovery packet #' + str(stage))

                if stage == 4:
                    hubsan_id = (resp[2] << 24) | (resp[3] << 16) | (resp[4] << 8)  | resp[5]
                    logging.debug('hubsan id: ' + str(hubsan_id))
                    break
                else:
                    stage = stage + 1
                    logging.debug('sending discovery packet #' + str(stage))
        logging.debug('handshake 1 completed')

        # setting session id
        a7105.write_id(hubsan_id)

        # HANDSHAKE 2
        logging.debug('starting handshake 2')
        while self.__discovery(1) == False: continue
        logging.debug('handshake 2 completed')

        # HANDSHAKE 3
        logging.debug('starting handshake 3')
        while True:
            resp = self.__discovery(0x9)
            if resp:
                state = resp[1]
                logging.debug('binding state: ' + str(state))
                if state == 0x09:
                    break
        logging.debug('handshake 3 completed')

        time.sleep(0.5)
        # wait a bit before sending commands
        a7105.set_register(Registers.CODE1, 0x0F)
        self.__safety()

        # start the control thread
        __thread = threading.Thread(target=self.__worker)
        __thread.start()

    """ resume a connection with a quadcopter """
    def resume(self, session_id, channel):
        self.session_id = session_id
        self.channel = channel

        a7105.write_id(self.session_id)
        a7105.set_channel(self.channel)

    """ adds the checksum to the packet and sends it """
    def send_packet(self, packet):
        # add checksum
        packet.append(crc(packet))
        a7105.strobe(State.STANDBY)
        a7105.write_data(packet)
        a7105.strobe(State.TX)
        time.sleep(0.002)
        for send_n in xrange(4):
            if a7105.get_register(Registers.MODE) & 1 == 0:
                return
        raise Exception("Sending did not complete.")

    """ stops the worker thread """
    def stop(self):
        if self.__thread != None:
            self.__running = False
            self.__thread.join()

    """ sends a control packet every 10ms """
    def __worker(self):
        self.__running = True
        while self.__running:
            self.__control()
            time.sleep(0.01)

    """ sends a control packet """
    def __control(self):
        throttle = lerp(clamp(self.throttle, 0, 1), 0x0, 0xFF)
        # todo: expert mode lerp from x0 to xFF
        yaw = lerp(clamp(self.yaw, 0, 1), 0x40, 0xC0)
        pitch = lerp(clamp(self.pitch, 0, 1), 0x40, 0xC0)
        roll = lerp(clamp(self.roll, 0, 1), 0x40, 0xC0)
        flags = 0x2 | (0 if self.leds else 0x4) | (0x8 if self.flips else 0)

        packet = [0x20, 0x0, throttle, 0x0, yaw, 0x0, pitch, 0x0, roll, flags,
                  0x64, 0xDB, 0x04, 0x26, 0x79] # tx id?
        self.send_packet(packet)

    """ sends 100 packets with 0 throttle """
    def __safety(self):
        logging.debug('sending safety packets')
        for i in xrange(100):
            self.throttle = 0
            self.__control()
            time.sleep(0.01)
        logging.debug('safety completed')

    """ sets up the a7105 registers and calibrates it """
    def __setup_a7105(self):
        a7105.strobe(State.STANDBY)
        # auto RSSI measurement, auto IF Offset, FIFO mode enabled
        a7105.set_register(Registers.MODE_CTL, 0b01100011)
        # set FIFO length to 16 bytes (0x0f + 1)
        a7105.set_register(Registers.FIFO1, 0b1111);
        # use crystal oscillator, CLK divider = /2.
        a7105.set_register(Registers.CLOCK, 0b0101);

        # sanity check
        if a7105.get_register(Registers.CLOCK) != 0x05:
          raise Exception('Sanity check failed. Check wiring.')

        # set data rate to 25kbps.
        a7105.set_register(Registers.DATA_RATE, 0b0100);
        # frequency deviation: 186KHz
        a7105.set_register(Registers.TX2, 0b00101011);
        # BPF bandwidth = 500 KHz.
        a7105.set_register(Registers.RX, 0b01100010);
        # manual VGA, Mixer Gain: 24dB, LNA gain: 24dB.
        a7105.set_register(Registers.RX_GAIN1, 0b10000000);
        # set some reserved constants
        a7105.set_register(Registers.RX_GAIN4, 0b1010);
        # select ID code length of 4, preamble length of 4
        a7105.set_register(Registers.CODE1, 0b0111);
        # set demodulator DC estimation average mode,
        # ID code error tolerance = 1 bit, 16 bit preamble pattern detection length
        a7105.set_register(Registers.CODE2, 0b00010111);
        # set constants
        a7105.set_register(Registers.RX_TEST1, 0b01000111);

        a7105.calibrate()
        a7105.set_power(Power._30mW)
        a7105.strobe(State.STANDBY)

    """ sends a discovery packet and returns the response """
    def __discovery(self, stage):
        packet = [stage,                            # handshake state
                  self.channel,                     # selected channel ID
                  (self.session_id >> 24) & 0xFF,   # session ID
                  (self.session_id >> 16) & 0xFF,
                  (self.session_id >> 8) & 0xFF,
                  (self.session_id) & 0xFF,
                  0x0, 0x0, 0x0, 0x0, 0x0,          # unused
                  0x0, 0x0, 0x0, 0x0]               # tx id?
        self.send_packet(packet)
        send_time = time.time()

        # poll for 15ms for the response
        a7105.strobe(State.RX)
        while time.time() < send_time + 0.015:
            if a7105.get_register(Registers.MODE) & 1 == 0:
                packet = a7105.read_data(16)
                return packet
        return None
