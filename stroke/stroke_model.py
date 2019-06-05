"""
Umbrella class to hold and run stroke triage problems
"""
import numpy as np
from . import costs, times, ais_outcomes, cohort, results, stroke_center as sc
import pandas as pd

class StrokeModel:
    """Store patient and hospital information and run the model"""

    @property
    def hospitals(self):
        """A list of all hospitals with valid associated travel times."""
        return [x for x in self._hospitals if not np.isnan(x.time)]

    @property
    def primaries(self):
        """A list of all primary centers with valid travel time."""
        return [x for x in self.hospitals if
                x.center_type is sc.CenterType.PRIMARY]

    @property
    def comprehensives(self):
        """A list of all comprehensive centers with valid travel time."""
        return [x for x in self.hospitals if
                x.center_type is sc.CenterType.COMPREHENSIVE]

    def __init__(self, patient, hospitals, threshold_ICER=1000000):
        """
        Generate model for given patient and hospitals. Hospitals may not
            have correct travel times set yet.
        """
        self._patient = patient
        self._hospitals = hospitals
        self._threshold_ICER = threshold_ICER

    def set_times(self, times):
        '''
        Given a series with center_id indices and travel time values, update
            primaries and comprehensives to use these times
        '''
        for center in self._hospitals:
            center_id = str(center.center_id)
            if center_id in times:
                try:
                    center.time = float(times[center_id])
                except ValueError:
                    center.time = np.NaN
            else:
                center.time = np.NaN

    def run(self, n=1000, add_time_uncertainty=True, add_lvo_uncertainty=True,
            fix_performance=False):
        """Run the model"""
        costs.Costs.inflate(2016)

        ais_times = times.IschemicTimes(self._patient, self.hospitals, n,
                                        add_time_uncertainty,
                                        add_lvo_uncertainty,
                                        fix_performance)
        ais_model = ais_outcomes.IschemicModel(ais_times)
        outcomes = ais_model.run_all_strategies()
        markov = cohort.Population(self._patient, outcomes)
        markov.analyze()
        return results.Results(markov)


    def run_new(self, n=1000, add_time_uncertainty=True, add_lvo_uncertainty=True,
            fix_performance=False):
        """Run the model, determine num of simulation by convergence"""
        costs.Costs.inflate(2016)
        convergence = False

        n_sim = int(n/2)
        c =0
        while not convergence:
            ais_times = times.IschemicTimes(self._patient, self.hospitals, n_sim,
                                            add_time_uncertainty,
                                            add_lvo_uncertainty,
                                            fix_performance)
            ais_model = ais_outcomes.IschemicModel(ais_times)
            outcomes = ais_model.run_all_strategies()
            markov = cohort.Population(self._patient, outcomes)
            markov.analyze()
            markov_results = results.Results(markov)
            cbc = markov_results.counts_by_center
            cbc = {str(center): count for center, count in cbc.items()}
            df_cbc = pd.DataFrame.from_dict(cbc,orient='index',columns=['count'])/n_sim
            if c > 0:
                convergence = ((df_cbc-old_df_cbc).abs().max() < .01).any()
            elif c > 19:
                convergence = True # repeat the runs 20 times max
            n_sim *=2
            c+=1
            old_df_cbc = df_cbc
            if not convergence: print(f'repeating for nsim of {n_sim}')
        return markov_results
