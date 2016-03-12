class Registers:
    MODE = 0x00
    MODE_CTL = 0x01
    CALC = 0x02
    FIFO1 = 0x03
    FIFO2 = 0x04
    FIFO_DATA = 0x05
    ID_DATA = 0x06
    RC_OSC_1 = 0x07
    RC_OSC_2 = 0x08
    RC_OSC_3 = 0x09
    CKO_PIN = 0x0A
    GPIO1 = 0x0B
    GPIO2 = 0x0C
    CLOCK = 0x0D
    DATA_RATE = 0x0E
    PLL1 = 0x0F
    PLL2 = 0x10
    PLL3 = 0x11
    PLL4 = 0x12
    PLL5 = 0x13
    TX1 = 0x14
    TX2 = 0x15
    DELAY1 = 0x16
    DELAY2 = 0x17
    RX = 0x18
    RX_GAIN1 = 0x19
    RX_GAIN2 = 0x1A
    RX_GAIN3 = 0x1B
    RX_GAIN4 = 0x1C
    RSSI = 0x1D
    ADC = 0x1E
    CODE1 = 0x1F
    CODE2 = 0x20
    CODE3 = 0x21
    IF1 = 0x22
    IF2 = 0x23
    VCO = 0x24
    VCO1 = 0x25
    VCO2 = 0x26
    BATTERY = 0x27
    TX_TEST = 0x28
    RX_TEST1 = 0x29
    RX_TEST2 = 0x2A
    CPC = 0x2B
    CRYSTAL_TEST = 0x2C
    PLL_TEST = 0x2D
    VCO_TEST1 = 0x2E
    VCO_TEST2 = 0x2F
    IFAT = 0x30
    RSCALE = 0x31
    FILTER_TEST = 0x32

class State:
    SLEEP = 0x80
    IDLE = 0x90
    STANDBY = 0xA0
    PLL = 0xB0
    RX = 0xC0
    TX = 0xD0
    RST_WRPTR = 0xE0
    RST_RDPTR = 0xF0

class Power:
    _100uW = 0
    _300uW = 1
    _1mW   = 2
    _3mW   = 3
    _10mW  = 4
    _30mW  = 5
    _100mW = 6
    _150mW = 7

# contains PAC and TBG values
power_enums = {}
power_enums[Power._100uW] = ( 0, 0 )
power_enums[Power._300uW] = ( 0, 1 ) # datasheet recommended
power_enums[Power._1mW]   = ( 0, 2 )
power_enums[Power._3mW]   = ( 0, 4 )
power_enums[Power._10mW]  = ( 1, 5 )
power_enums[Power._30mW]  = ( 2, 7 ) # looks like a good value
power_enums[Power._100mW] = ( 3, 7 ) # datasheet recommended
power_enums[Power._150mW] = ( 3, 7 ) # datasheet recommended