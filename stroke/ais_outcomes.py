"""
Model short term outcome distribution for a patient under all available
    strategies
"""
import numpy as np
from . import constants
from .constants import StrategyKind


class Outcome:
    """
    Stores probability of a good outcome, probability of tPA, probability of
        EVT, and probability of transfer for a class of strategies. Entries are
        arrays with rows for model runs and columns for destination hospitals
        or lower-dimensional representation that can be broadcast to the full
        array (in the case where the value is the same for all hospitals and/or
        model runs).
    """

    @property
    def shape(self):
        """Shape of outcome (number of model runs, number of strategies)"""
        return self.p_good.shape

    def __init__(self, p_good, p_tpa, p_evt, p_transfer, strategies):
        """
        Store outcomes for a set of strategies. All probabilities should
            have the shape (number of model runs, number of strategies)
            or be broadcastable to it.
        """
        self.p_good = p_good
        self.p_tpa = p_tpa
        self.p_evt = p_evt
        self.p_transfer = p_transfer
        self.strategies = strategies

    def __add__(self, other):
        """
        Combine outcomes for multiple sets of strategies
        """
        p_good = np.concatenate([self.p_good, other.p_good], axis=1)
        p_tpa = np.concatenate([self._reshape(self.p_tpa),
                                other._reshape(other.p_tpa)], axis=1)
        p_evt = np.concatenate([self._reshape(self.p_evt),
                                other._reshape(other.p_evt)], axis=1)
        p_transfer = np.concatenate([self._reshape(self.p_transfer),
                                     other._reshape(other.p_transfer)], axis=1)
        strategies = self.strategies + other.strategies
        return Outcome(p_good, p_tpa, p_evt, p_transfer, strategies)

    def _reshape(self, array):
        return np.broadcast_arrays(array, self.p_good)[0]


class IschemicModel:

    def __init__(self, times):
        """
        Initialize with an IschemicTimes object storing times to be used to
            generate outcome distributions
        """
        self.times = times

    def run_all_strategies(self):
        """Compute outcome for all possible strategies"""
        primary_outcomes = self.run_primaries()
        drip_and_ship_outcomes = self.run_drip_and_ship()
        comprehensive_outcomes = self.run_comprehensives()
        return (primary_outcomes + drip_and_ship_outcomes +
                comprehensive_outcomes)

    def run_primaries(self):
        """
        Compute outcome for going only to the primary center, for each
            primary center.
        """
        p_good = self._get_p_good(self.times.onset_needle_primary) # probability of a good outcome
        p_tpa = 1
        p_evt = 0
        p_transfer = 0 # no transfer, this is handled in run_drip_and_ship
        strategies = self.times.get_strategies(StrategyKind.PRIMARY)

        return Outcome(p_good, p_tpa, p_evt, p_transfer, strategies)

    def run_comprehensives(self):
        """
        Compute outcome for going directly to comprehensive center, for
            each comprehensive center.
        """
        onset_needle = self.times.onset_needle_comprehensive
        onset_puncture = self.times.onset_evt_noship
        p_good = self._get_p_good(onset_needle, onset_puncture)
        p_tpa = np.where(onset_needle < constants.time_limit_tpa(), 1, 0)
        p_evt = np.where(onset_puncture < constants.time_limit_evt(),
                         self.times.p_lvo, 0)
        p_transfer = 0

        strategies = self.times.get_strategies(StrategyKind.COMPREHENSIVE)

        return Outcome(p_good, p_tpa, p_evt, p_transfer, strategies)

    def run_drip_and_ship(self):
        """
        Compute outcome for going to primary center then transfering to a
            comprehensive center.
        """
        onset_needle = self.times.onset_needle_primary
        onset_puncture = self.times.onset_evt_ship
        # If there isn't time to receive EVT after a transfer, then drip and
        #   ship isn't a viable strategy so we set p_good to NaN
        evt_possible = _compare_nan_array(np.less,
                                          onset_puncture,
                                          constants.time_limit_evt())
        tpa_possible = onset_needle < constants.time_limit_tpa()
        p_good = np.where(evt_possible,
                          self._get_p_good(onset_needle, onset_puncture),
                          np.NaN)
        p_tpa = np.where(tpa_possible, 1, 0)
        p_evt = np.where(evt_possible, self.times.p_lvo, 0)
        # We assume transfer happens, since otherwise this is just a repeat of
        #   primary strategy. Ideally we might model an estimated
        #   onset_puncture based on information avaible at the transfer
        #   decision time.
        p_transfer = 1

        strategies = self.times.get_strategies(StrategyKind.DRIP_AND_SHIP)

        return Outcome(p_good, p_tpa, p_evt, p_transfer, strategies)

    def _get_p_good(self, onset_to_tpa, onset_to_evt=None):
        """
        Get the probability of a good outcome given arrays of onset to
            treatment times.
        """
        severity = self.times.patient.severity
        baseline_p_good = severity.p_good_outcome_ais_no_lvo(onset_to_tpa)

        if onset_to_evt is None:
            # No EVT, outcome just depends on time to tPA
            return baseline_p_good

        p_rep_endo = severity.p_reperfusion_endovascular()
        p_reperfused = (self.times.p_lvo * p_rep_endo)
        evt_possible = _compare_nan_array(np.less,
                                          onset_to_evt,
                                          constants.time_limit_evt())
        p_good_post_evt = np.where(
            evt_possible,
            severity.p_good_outcome_post_evt_success(
                onset_to_evt
            ),
            baseline_p_good
        )
        higher_p_good = np.maximum(p_good_post_evt, baseline_p_good)

        return (higher_p_good * p_reperfused +
                baseline_p_good * (1 - p_reperfused))


def _compare_nan_array(func, array, threshold):
    '''
    Perform the comparison func(array, threshold) only for non-NaN elements
        of array. False for NaN elements
        From https://stackoverflow.com/questions/47340000/
        how-to-get-rid-of-runtimewarning-invalid-value-encountered-in-greater
    '''
    out = ~np.isnan(array)
    out[out] = func(array[out], threshold)
    return out
