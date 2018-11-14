"""
Cost values, including handling of inflation
"""
from . import inflation
from .constants import States


class BaseYears:
    """
    Object recording base year for each cost to use in inflation adjustment.
    """

    def __init__(self, year=None):
        """Initialize with hard coded years or known constant year for all"""
        if year is None:
            self.ischemic = 2014
            self.ich = 2008
            self.annual = 2014
            self.death = 2008
            self.ivt = 2014
            self.evt = 2014
            self.transfer = 2010
        else:
            self.ischemic = year
            self.ich = year
            self.annual = year
            self.death = year
            self.ivt = year
            self.evt = year
            self.transfer = year


class Costs:

    TARGET_YEAR = inflation.Conversion.LAST_YEAR
    YEAR = None

    # 2014, Dewilde
    DAYS_90_ISCHEMIC = {
        States.GEN_POP: 0,
        States.MRS_0: 6302,
        States.MRS_1: 9448,
        States.MRS_2: 14918,
        States.MRS_3: 26218,
        States.MRS_4: 32502,
        States.MRS_5: 26071
    }

    # 2008, Christensen
    DAYS_90_ICH = {
        States.GEN_POP: 0,
        States.MRS_0: 9500,
        States.MRS_1: 15500,
        States.MRS_2: 18700,
        States.MRS_3: 27400,
        States.MRS_4: 27300,
        States.MRS_5: 27300
    }

    # 2014, Dewilde
    ANNUAL = {
        States.GEN_POP: 0,
        States.MRS_0: 2921,
        States.MRS_1: 3905,
        States.MRS_2: 6501,
        States.MRS_3: 16922,
        States.MRS_4: 42335,
        States.MRS_5: 39723
    }

    # 2008, Christensen
    DEATH = 8100

    # 2014, Sevick
    IVT = 13419

    # 2014, Kleindorfer
    EVT = 6400

    # 2010, Mohr
    TRANSFER = 763

    @staticmethod
    def inflate(target_year):
        # print(f'inflating to {target_year}')
        if Costs.YEAR == target_year:
            # print('already there, doing nothing')
            # Don't do anything if we've already inflated to the desired year
            return

        base_years = BaseYears(Costs.YEAR)

        for state in Costs.DAYS_90_ISCHEMIC:
            Costs.DAYS_90_ISCHEMIC[state] = (inflation.Conversion.run(
                base_years.ischemic, target_year,
                Costs.DAYS_90_ISCHEMIC[state]))
        for state in Costs.DAYS_90_ICH:
            Costs.DAYS_90_ICH[state] = (inflation.Conversion.run(
                base_years.ich, target_year, Costs.DAYS_90_ICH[state]))
        for state in Costs.ANNUAL:
            Costs.ANNUAL[state] = (inflation.Conversion.run(
                base_years.annual, target_year, Costs.ANNUAL[state]))
        Costs.DEATH = inflation.Conversion.run(base_years.death, target_year,
                                               Costs.DEATH)
        Costs.IVT = inflation.Conversion.run(base_years.ivt, target_year,
                                             Costs.IVT)
        Costs.EVT = inflation.Conversion.run(base_years.evt, target_year,
                                             Costs.EVT)
        Costs.TRANSFER = inflation.Conversion.run(base_years.transfer,
                                                  target_year,
                                                  Costs.TRANSFER)

        Costs.YEAR = target_year


def cost_ivt():
    # print(f'Getting IVT costs {Costs.IVT}')
    return Costs.IVT


def cost_evt():
    # print(f'Getting EVT costs {Costs.EVT}')
    return Costs.EVT


def cost_transfer():
    # print(f'Getting transfer costs {Costs.TRANSFER}')
    return Costs.TRANSFER


def first_year_costs(states_hemorrhagic, states_ischemic):
    """Compute total first year costs for hemorrhagic and ischemic strokes"""
    cost = 0
    for state in range(States.DEATH):
        # capture all costs for living patients
        hemorrhagic_cost = ((90 / 360) * Costs.DAYS_90_ICH[state] +
                            ((360 - 90) / 360) * Costs.ANNUAL[state])
        cost += states_hemorrhagic[:, :, state] * hemorrhagic_cost
        ischemic_cost = ((90 / 360) * Costs.DAYS_90_ISCHEMIC[state] +
                         ((360 - 90) / 360) * Costs.ANNUAL[state])
        cost += states_ischemic[:, :, state] * ischemic_cost

    cost += states_hemorrhagic[:, :, States.DEATH] * Costs.DEATH
    cost += states_ischemic[:, :, States.DEATH] * Costs.DEATH
    return cost


def annual_costs(states):
    """Compute annual costs given mRS distributions"""
    cost = 0
    for state in range(States.DEATH):
        # capture all costs for living patients
        cost += states[:, :, state] * Costs.ANNUAL[state]

    # Should death costs be added in every year like this? As I read it
    #  states[:, :, States.DEATH] is all cumulative deaths, not new deaths
    cost += states[:, :, States.DEATH] * Costs.DEATH

    return cost
