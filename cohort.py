"""
Long term costs and QALYs via markov model simulation
"""
import numpy as np
import constants
from constants import States
from life_tables import LifeTables
import costs


class Population:
    """
    Store the cohorts for a set of model runs and strategies (of a particular
        kind), and run the markov model simulation.
    """

    END_AGE = 100

    def __init__(self, patient, ais_outcomes, horizon=None):
        """
        Initialize a cohort for a particular patient with given AIS outcomes
            for a particular kind of strategy.
        """
        self.start_age = patient.age
        self.sex = patient.sex
        self.severity = patient.severity
        self.strategy_kind = ais_outcomes.strategy_kind
        self.horizon = horizon
        self._break_into_states(ais_outcomes)

    def analyze(self):
        """
        Run full Markov analysis on this cohort, generating costs and QALYs
            for each model run and hospital
        """
        self._run_markov()
        self._get_qalys_per_year()
        self._get_costs_per_year()
        self.qalys = simpsons_1_3rd_correction(self._qalys_per_year,
                                               self.horizon)
        self.costs = simpsons_1_3rd_correction(self._costs_per_year,
                                               self.horizon)

    def _break_into_states(self, ais_outcomes):
        """
        Generate initial cohort states from AIS outcomes and compute first
            year costs.
        """
        call_population = 1
        pop_mimic = call_population * constants.p_call_is_mimic()
        pop_hemorrhagic = call_population * constants.p_call_is_hemorrhagic()
        pop_ischemic = call_population - pop_mimic - pop_hemorrhagic

        # Get the mRS breakdown for AIS patients
        ais_states = self.severity.break_up_ais_patients(ais_outcomes.p_good)

        # Remember to adjust for population of ischemic patients
        ais_states *= pop_ischemic

        # initialize the global state matrix with AIS patients
        states = ais_states.copy()

        # Now we need the mRS breakdown for patients with hemorrhagic strokes
        # Currently making the conservative estimate that there is no
        # difference in outcomes for ICH versus AIS patients, even though
        # there is evidence to suggest to suggest ICH patients do almost
        # about twice as well.
        # This estimate also adjusts hemorrhagic stroke outcomes based on
        # time to center.
        hemorrhagic_states = ais_states * pop_hemorrhagic
        states += hemorrhagic_states

        # We assume that mimics are at gen pop (headache, migraine, etc.)
        states[:, :, States.GEN_POP] += pop_mimic

        self.states = states

        # Get first year costs
        first_costs = costs.first_year_costs(hemorrhagic_states, ais_states)
        first_costs += costs.cost_ivt() * ais_outcomes.p_tpa * pop_ischemic
        first_costs += costs.cost_evt() * ais_outcomes.p_evt * pop_ischemic
        first_costs += (costs.cost_transfer() * ais_outcomes.p_transfer *
                        pop_ischemic)

        # Store costs as a list of arrays
        self._costs_per_year = [first_costs]

    def _run_markov(self):
        """
        Given starting states in self.states, generate a list of states for
            each year from start to END_AGE
        """
        self._states_per_year = [self.states.copy()]
        current_states = self.states
        current_age = self.start_age
        while current_age < Population.END_AGE:
            # We run a range up to death because we don't want to include death
            # since it only markovs to itself
            for state in range(States.DEATH):
                p_dead = LifeTables.adjusted_mortality(
                    self.sex, current_age, constants.hazard_mort(state)
                )
                deaths = current_states[:, :, state] * p_dead
                current_states[:, :, state] -= deaths
                current_states[:, :, States.DEATH] += deaths

            current_age += 1
            self._states_per_year.append(current_states.copy())

    def _get_qalys_per_year(self):
        """
        Generate a list of discounted quality-adjusted life years at each year
        """
        continuous_discount = 0.03
        discrete_discount = np.exp(continuous_discount) - 1
        qalys = []
        for year, states in enumerate(self._states_per_year):
            qaly = 0
            for state in range(constants.States.DEATH):
                qaly += states[:, :, state] * constants.utilities_mrs(state)
            # Discount
            qaly /= ((1 + discrete_discount)**year)
            qalys.append(qaly)

        self._qalys_per_year = qalys

    def _get_costs_per_year(self):
        """
        Generate a list of discounted costs at each year
        """
        continuous_discount = 0.03
        discrete_discount = np.exp(continuous_discount) - 1
        for year, states in enumerate(self._states_per_year):
            if year == 0:
                # First year costs are computed in _break_into_states
                continue
            yearly_costs = costs.annual_costs(states)
            yearly_costs /= ((1 + discrete_discount)**year)
            self._costs_per_year.append(yearly_costs)


def simpsons_1_3rd_correction(yearly_value, years_horizon=None):
    '''
    Returns the sum of the list of arrays inputted for either
    discounted costs or QALYs. Default is to run a lifetime horizon, but
    can run for the correction for any number of years as long as it is
    specified.
    '''
    multiplier = 1 / 3
    sum_ = yearly_value[0] * multiplier
    start_index = 1
    end_index = len(yearly_value) - 1
    if years_horizon is not None and years_horizon <= end_index:
        end_index = years_horizon
    # Since for in range in [a, b)
    for i in range(start_index, end_index + 1):
        if i == end_index:
            multiplier = 1 / 3
        else:
            if i % 2 == 0:
                multiplier = 2 / 3
            else:
                multiplier = 4 / 3
        sum_ += (yearly_value[i] * multiplier)
    return sum_
