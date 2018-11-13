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


def time_limit_tpa():
    return 270


def time_limit_evt():
    return 360


# PLUMBER Study
def p_call_is_mimic():
    # incude TIA
    return (1635 + 191) / 2402


# PLUMBER Study
def p_call_is_hemorrhagic():
    # include ICH and SAH
    return (16 + 85) / 2402


HAZARDS_MORTALITY = {
    States.GEN_POP: 1,
    States.MRS_0: 1.53,
    States.MRS_1: 1.52,
    States.MRS_2: 2.17,
    States.MRS_3: 3.18,
    States.MRS_4: 4.55,
    States.MRS_5: 6.55
}


def hazard_mort(mrs):
    '''
    Again keep it as a function so that it's easier to do sensitivity analyses
    later on.
    '''
    return HAZARDS_MORTALITY[mrs]


UTILITIES = {
    States.GEN_POP: 1.00,
    States.MRS_0: 1.00,
    States.MRS_1: 0.84,
    States.MRS_2: 0.78,
    States.MRS_3: 0.71,
    States.MRS_4: 0.44,
    States.MRS_5: 0.18
}


def utilities_mrs(mrs):
    return UTILITIES[mrs]
