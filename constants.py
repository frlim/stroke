"""
Fixed parameters and notational conveniences
"""
import enum


class Sex(enum.IntEnum):
    MALE = 0
    FEMALE = 1


class States(enum.IntEnum):
    '''
    Make the model a little easier to read
    '''
    GEN_POP = 0
    MRS_0 = 1
    MRS_1 = 2
    MRS_2 = 3
    MRS_3 = 4
    MRS_4 = 5
    MRS_5 = 6
    MRS_6 = 7
    DEATH = MRS_6
    NUMBER_OF_STATES = 8


class StrategyKind(enum.IntEnum):
    PRIMARY = 0
    COMPREHENSIVE = 1
    DRIP_AND_SHIP = 2
