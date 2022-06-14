from enum import Enum

class Device(Enum):
    ROUTER = 'ne.category.route'
    SWITCH = 'ne.category.switch'

class Slot(Enum):
    BOARD = 9 # inclui CPU e CLK
    POWER = 6
    FAN = 7
