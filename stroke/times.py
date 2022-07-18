"""
Model relevant hospital times for an AIS patient under all available
    strategies
"""
import numpy as np
from . import stroke_center as sc, constants, strategy


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
        return self._onset_evt_ship

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

        # Initialize empty cache dictionary for Strategy lists
        self._strategies = {}

    def get_strategies(self, strategy_kind):
        """
        Get a list of strategies of the appropriate kind, in the same
            order the strategies appear in onset to treatment time arrays.
        """
        if strategy_kind in self._strategies: # starts off empty
            return self._strategies[strategy_kind]

        # Direct to comprehensive center strategy
        if strategy_kind is constants.StrategyKind.COMPREHENSIVE:
            constructor = strategy.Strategy.comprehensive
            hospitals = self._comprehensives # list of all comprehensive hospitals with travel time value
        
        # Direct to primary center strategy
        elif strategy_kind is constants.StrategyKind.PRIMARY:
            constructor = strategy.Strategy.primary
            hospitals = self._primaries # list of all primary hospitals with travel time value

        # Drip at primary center and ship to comprehensive strategy
        elif strategy_kind is constants.StrategyKind.DRIP_AND_SHIP:
            constructor = strategy.Strategy.drip_and_ship
            hospitals = self._primaries # list of all primary hospitals with travel time value
        
        else:
            raise ValueError(f'Unrecognized strategy kind {strategy_kind}')

        # List of all strategies names: Primary to _, Comprehension to _, Drink and Ship _ to _ 
        strategies = [constructor(hospital) for hospital in hospitals]
        self._strategies[strategy_kind] = strategies
        return strategies

    def _process_hospitals(self, hospitals, n, add_time_uncertainty,
                           fix_performance):
        if fix_performance:
            dtn_perf = np.random.uniform(0, 1, n)
            dtp_perf = np.random.uniform(0, 1, n)
        else:
            dtn_perf = None
            dtp_perf = None
        primaries = []
        comprehensives = []
        for hospital in hospitals:
            hospital.set_door_to_needle(n, add_time_uncertainty, dtn_perf)
            hospital.set_travel_time(n)
            if hospital.center_type is sc.CenterType.PRIMARY:
                # also initialize transfer destination times since they may not
                #   be in self.comprehensives
                td = hospital.transfer_destination
                if td is not None:
                    td.set_door_to_needle(n, add_time_uncertainty, dtn_perf)
                    td.set_door_to_puncture(n, add_time_uncertainty, dtp_perf)
                primaries.append(hospital)
            elif hospital.center_type is sc.CenterType.COMPREHENSIVE:
                hospital.set_door_to_puncture(n, add_time_uncertainty,
                                              dtp_perf)
                comprehensives.append(hospital)
        self._primaries = primaries
        self._comprehensives = comprehensives

    def _compute_onset_needle_primary(self):
        self._onset_needle_primary = self._onset_needle(self._primaries)

    def _compute_onset_needle_comprehensive(self):
        self._onset_needle_comprehensive = self._onset_needle(
            self._comprehensives
        )

    def _onset_needle(self, hospitals):
        travel = []
        dtn = []
        for hospital in hospitals:
            travel.append(hospital.time)
            dtn.append(hospital.door_to_needle)
        # time_to_hospital = np.hstack(travel)
        time_to_hospital = np.dstack(travel)[0]
        dtn = np.dstack(dtn)[0]
        # print("Travel time: {}".format(time_to_hospital.shape))
        # print("DTN time: {}".format(dtn.shape))

        return self.patient.symptom_time + time_to_hospital + dtn

    def _compute_onset_evt_noship(self):
        travel = []
        dtp = []
        for comp in self._comprehensives:
            travel.append(comp.time)
            dtp.append(comp.door_to_puncture)
        # time_to_hospital = np.hstack(travel)
        time_to_hospital = np.dstack(travel)[0]
        dtp = np.dstack(dtp)[0]

        time = self.patient.symptom_time + time_to_hospital + dtp
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
                null_ttp = np.broadcast_arrays(np.NaN,
                                               primary.door_to_needle)[0]
                transfer_to_puncture.append(null_ttp)
            else:
                comp = primary.transfer_destination
                transfer_time.append(primary.transfer_time)
                transfer_to_puncture.append(comp.door_to_puncture -
                                            primary.door_to_needle)
        # to_primary = np.hstack(to_primary)
        to_primary = np.dstack(to_primary)[0]
        door_to_needle = np.dstack(door_to_needle)[0]
        transfer_time = np.hstack(transfer_time)
        transfer_to_puncture = np.dstack(transfer_to_puncture)[0]
        # approximation of intrahospital time for transfer, which seems to
        #   cancel out here, so primary DTN doesn't impact drip and ship time
        #   to EVT. (Maybe this should use comp.door_to_needle instead?)
        self._onset_evt_ship = (
            self.patient.symptom_time + to_primary +
            door_to_needle + transfer_time + transfer_to_puncture
        )
