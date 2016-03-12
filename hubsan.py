from a7105_const import *
import a7105
import time
import struct
import math
import random
import logging

def crc(packet):
    total = 0
    for char in packet:
        total += char
    return (256 - (total % 256)) & 0xff

class Hubsan:
    ALLOWED_CHANNELS = [ 0x14, 0x1e, 0x28, 0x32, 0x3c, 0x46, 0x50, 0x5a, 0x64, 0x6e, 0x78, 0x82 ]
    ID = 0x55201041

    def __init__(self, copter_id):
        # generate a random session ID
        self.session_id = random.randint(0, 2147483647)
        self.channel, = random.sample(Hubsan.ALLOWED_CHANNELS, 1)

    def control(self, throttle, yaw, pitch, roll, led=True):
        flags = 0xE if led else 0xA
        packet = [0x20, 0x0, throttle, 0x0, yaw, 0x0, pitch, 0x0, roll, flags,
                  0x64, 0xDB, 0x04, 0x26, 0x79]
        self.send_packet(packet)

    def bind(self):
        a7105.write_id(0x55201041)
        a7105.set_channel(self.channel)

        logging.debug('Binding sequence started')
        logging.debug('Starting handshake 1')
        logging.debug('Broadcasting discovery #1')
        stage = 0x1
        tmp_id = 0

        while True:
            resp = self.__discovery(stage)
            if resp != False:
                logging.debug('Received discovery #' + str(resp[0]))
                stage = resp[0] + 1
                if stage == 5:
                    tmp_id = ((resp[2] << 24) | (resp[3] << 16) |
                             (resp[4] << 8)  | resp[5])
                    break
                else:
                    logging.debug('Sending discovery #' + str(stage))
        logging.debug('Handshake 1 completed')

        a7105.write_id(tmp_id)
        logging.debug('Starting handshake 2')
        while self.__discovery(0x1) == False:
            continue
        logging.debug('Handshake 2 completed')

        logging.debug('Starting handshake 3')
        while True:
            resp = self.__discovery(0x09)
            if resp:
                state = resp[1]
                logging.debug('Binding state: ' + str(state))
                if state == 0x09:
                    break
        logging.debug('Handshake 3 completed')
        time.sleep(0.5)
        a7105.set_register(Registers.CODE1, 0x0F)

    def safety(self):
        logging.debug('Sending safety signals')
        for i in xrange(100):
            self.control(0, 0, 0, 0) # send 0 throttle for 100 cycles
        logging.debug('Safety completed')

    def __discovery(self, stage):
        packet = [stage,                             # handshake state
                  self.channel,                     # selected channel ID
                  (self.session_id >> 24) & 0xFF,   # session ID
                  (self.session_id >> 16) & 0xFF,
                  (self.session_id >> 8) & 0xFF,
                  (self.session_id) & 0xFF,
                  0x0, 0x0, 0x0, 0x0, 0x0,          # unused
                  0x0, 0x0, 0x0, 0x0]
        self.send_packet(packet)
        send_time = time.time()

        a7105.strobe(State.RX)
		# poll for 15 ms for the response
        while time.time() < send_time + 0.015:
            if a7105.get_register(Registers.MODE) & 1 == 0:
                packet = a7105.read_data(16)
                return packet
        return False

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
