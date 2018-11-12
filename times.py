"""
Model relevant hospital times for an AIS patient under all available
    strategies
"""
import numpy as np
import stroke_center as sc


class IschemicTimes:
    """
    Model relevant times for a patient with an acute ischemic stroke
    """

    @property
    def onset_needle_primary(self):
        """
        All onset to needle times for primary centers, as an array where
            each row is a model run and each column is a primary center, in
            the order they appear in self._primaries.
        """
        return self._onset_needle_primary

    @property
    def onset_needle_comprehensive(self):
        """
        All onset to needle times for comprehensive centers, as an array where
            each row is a model run and each column is a comprehensive center,
            in the order they appear in self._comprehensives.
        """
        return self._onset_needle_comprehensive

    @property
    def onset_evt_noship(self):
        """
        All onset to EVT times for comprehensive centers, as an array where
            each row is a model run and each column is a comprehensive center,
            in the order they appear in self._comprehensives.
        """
        return self._onset_evt_noship

    @property
    def onset_evt_ship(self):
        """
        All onset to EVT times for drip and ship, as an array where
            each row is a model run and each column is a primary center,
            in the order they appear in self._primaries. Values are NaN if no
            transfer destination exists
        """
        return self._onset_evt_noship

    def __init__(self, patient, hospitals, n, add_time_uncertainty,
                 add_lvo_uncertainty, fix_performance=False):
        """
        Initialize with patient information and all potential destination
            hospitals. Hospitals should have travel time information, and
            primary centers treated as drip and ship candidates should have
            transfer destination and times.
            n -- number of randomized simulations to include
            add_time_uncertainty -- randomize intra-hospital times
            add_lvo_uncertainty -- randomize probability of an LVO
            fix_performance -- if True all hospitals have intrahospital times
                                at the same percentile of their distribution,
                                otherwise all draws are independent
        """
        self.patient = patient

        # Generate intra-hospital times
        self._process_hospitals(hospitals, n, add_time_uncertainty,
                                fix_performance)

        # Compute onset to treatment times
        self._compute_onset_needle_primary()
        self._compute_onset_needle_comprehensive()
        self._compute_onset_evt_noship()
        self._compute_onset_evt_ship()

        # Generate probability of LVO
        self.p_lvo = patient.severity.prob_LVO_given_AIS(n,
                                                         add_lvo_uncertainty)

    def _process_hospitals(self, hospitals, n, add_time_uncertainty,
                           fix_performance):
        if fix_performance:
            dtn_perf = np.random.uniform(0, 1)
            dtp_perf = np.random.uniform(0, 1)
        else:
            dtn_perf = None
            dtp_perf = None
        primaries = []
        comprehensives = []
        for hospital in hospitals:
            hospital.set_door_to_needle(n, add_time_uncertainty, dtn_perf)
            if hospital.center_type is sc.CenterType.PRIMARY:
                # also initialize transfer destination times since they may not
                #   be in self.comprehensives
                td = hospital.transfer_destination
                if td is not None:
                    td.set_door_to_needle(add_time_uncertainty, dtn_perf)
                    td.set_door_to_puncture(add_time_uncertainty, dtp_perf)
                primaries.append(hospital)
            elif hospital.center_type is sc.CenterType.COMPREHENSIVE:
                hospital.set_door_to_puncture(add_time_uncertainty, dtp_perf)
                comprehensives.append(hospital)
        self._primaries = primaries
        self._comprehensives = comprehensives

    def _compute_onset_needle_primary(self):
        self._onset_needle_primary = self._onset_needle(self._primaries)

    def _compute_onset_needle_comprehensive(self):
        self._onset_needle_comprehensive = self._onset_needle(
            self.comprehensives
        )

    def _onset_needle(self, hospitals):
        travel = []
        dtn = []
        for hospital in hospitals:
            travel.append(hospital.time)
            dtn.append(hospital.door_to_needle)
        time_to_hospital = np.stack(travel)
        dtn = np.stack(dtn, axis=1)

        return self.patient.time_since_symptoms + time_to_hospital + dtn

    def _compute_onset_evt_noship(self):
        travel = []
        dtp = []
        for comp in self._comprehensives:
            travel.append(comp.time)
            dtp.append(comp.door_to_puncture)
        time_to_hospital = np.stack(travel)
        dtp = np.stack(dtp, axis=1)

        time = self.patient.time_since_symptoms + time_to_hospital + dtp
        self._onset_evt_noship = time

    def _compute_onset_evt_ship(self):
        to_primary = []
        door_to_needle = []
        transfer_time = []
        transfer_to_puncture = []
        for primary in self._primaries:
            to_primary.append(primary.time)
            door_to_needle.append(primary.door_to_needle)
            if primary.transfer_destination is None:
                transfer_time.append(np.NaN)
                transfer_to_puncture.append(np.NaN)
            else:
                comp = primary.transfer_destination
                transfer_time.append(primary.transfer_time)
                transfer_to_puncture.append(comp.door_to_puncture -
                                            primary.door_to_needle)
        to_primary = np.stack(to_primary)
        door_to_needle = np.stack(door_to_needle, axis=1)
        transfer_time = np.stack(transfer_time)
        transfer_to_puncture = np.stack(transfer_to_puncture, axis=1)
        # approximation of intrahospital time for transfer, which seems to
        #   cancel out here, so primary DTN doesn't impact drip and ship time
        #   to EVT. (Maybe this should use comp.door_to_needle instead?)
        self._onset_evt_ship = (
            self.patient.time_since_symptoms + to_primary +
            door_to_needle + transfer_time + transfer_to_puncture
        )
