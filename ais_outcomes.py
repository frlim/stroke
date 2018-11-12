"""
Model short term outcome distribution for a patient under all available
    strategies
"""
import numpy as np
import collections
import constants


Outcome = collections.namedtuple('Outcome',
                                 ['p_good', 'p_tpa', 'p_evt', 'p_transfer'])
Outcome.__doc__ == """
Stores probability of a good outcome, probability of tPA, probability of EVT,
    and probability of transfer for a class of stratgies. Entries are
    arrays with rows for model runs and columns for destination hospitals or
    lower-dimensional representation that can be broadcast to the full array
    (in the case where the value is the same for all hospitals and/or model
    runs).
"""


class IschemicModel:

    def __init__(self, times):
        """
        Initialize with an IschemicTimes object storing times to be used to
            generate outcome distributions
        """
        self.times = times

    def run_primaries(self):
        """
        Compute outcome for going only to the primary center, for each
            primary center.
        """
        p_good = self._get_p_good(self.times.onset_needle_primary)
        p_tpa = 1
        p_evt = 0
        p_transfer = 0

        return Outcome(p_good, p_tpa, p_evt, p_transfer)

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

        return Outcome(p_good, p_tpa, p_evt, p_transfer)

    def run_drip_and_ship(self):
        """
        Compute outcome for going to primary center then transfering to a
            comprehensive center.
        """
        onset_needle = self.times.onset_needle_primary
        onset_puncture = self.times.onset_evt_ship
        p_good = self._get_p_good(onset_needle, onset_puncture)
        p_tpa = np.where(onset_needle < constants.time_limit_tpa(), 1, 0)
        p_evt = np.where(onset_puncture < constants.time_limit_evt(),
                         self.times.p_lvo, 0)
        # We assume transfer happens, since otherwise this is just a repeat of
        #   primary strategy. Ideally we might model an estimated
        #   onset_puncture based on information avaible at the transfer
        #   decision time.
        p_transfer = 1

        return Outcome(p_good, p_tpa, p_evt, p_transfer)

    def _get_p_good(self, onset_to_tpa, onset_to_evt=None):
        """
        Get the probability of a good outcome given arrays of onset to
            treatment times.
        """
        baseline_p_good = self.patient.severity.p_good_outcome_ais_no_lvo(
            onset_to_tpa
        )

        if onset_to_evt is None:
            # No EVT, outcome just depends on time to tPA
            return baseline_p_good

        severity = self.patient.severity
        p_rep_endo = severity.p_reperfusion_endovascular()
        p_reperfused = (self.times.p_lvo * p_rep_endo)
        p_good_post_evt = np.where(
            onset_to_evt < constants.time_limit_evt(),
            severity.p_good_outcome_post_evt_success(
                onset_to_evt
            ),
            baseline_p_good
        )
        higher_p_good = np.maximum(p_good_post_evt, baseline_p_good)

        return (higher_p_good * p_reperfused +
                baseline_p_good * (1 - p_reperfused))
