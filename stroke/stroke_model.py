"""
Umbrella class to hold and run stroke triage problems
"""
import numpy as np
from . import costs, times, ais_outcomes, cohort, results, stroke_center as sc
import pandas as pd
import os

class StrokeModel:
    """Store patient and hospital information and run the model"""

    @property
    def hospitals(self):
        """A list of all hospitals with valid associated travel times."""
        return [x for x in self._hospitals if not x.time_dist.isnan()]

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
            primaries and comprehensives to use these times.
        Each time value must be a list of [no_traffic_time,traffic_time]
        '''
        for center in self._hospitals: # iterate through each hospital class instance
            center_id = str(center.center_id)
            if center_id in times:
                center.time_dist = sc.TravelTimeDistribution(*times[center_id]) # input: [min_time, max_time]
            else:
                center.time_dist = None

    def run(self, n=1000, add_time_uncertainty=True, add_lvo_uncertainty=True,
            fix_performance=False):
        """Run the model"""
        costs.Costs.inflate(2016) # what year to inflate costs

        # Acute ischemic stroke, model times
        # Give patient profile and list of potential hospital destinations
        # n = number of randomized simulations
        # Generates intra-hospital times, onset to treatment times, probability of LVO
        ais_times = times.IschemicTimes(self._patient, self.hospitals, n,
                                        add_time_uncertainty,
                                        add_lvo_uncertainty,
                                        fix_performance)
        
        # Stores times to generate outcome distributions
        ais_model = ais_outcomes.IschemicModel(ais_times)
        
        # Get all possible strategies and their outcomes: primary, drip and ship, comprehensive
        # Runs functions from IschemicModel class
        outcomes = ais_model.run_all_strategies() # output Outcome object of all strategies
        
        # Stores patient information, can be run as markov to get LY, QALYs, costs, etc.
        markov = cohort.Population(self._patient, outcomes)
        # Analyze runs markov on patient, generating costs and qalys for each run/hospital
        markov.analyze()

        # results.Results tabulates output of markov.analyze()
        return results.Results(markov),markov,ais_times

    def _check_convergence(self,markov_results,n_sim,old_df_cbc=None):
        CONVERGENCE_THRESH = .01 # out of 1 (1%)
        cbc = {str(center): count for center, count in markov_results.counts_by_center.items()}
        df_cbc = pd.DataFrame.from_dict(cbc,orient='index',columns=['count'])/n_sim
        if old_df_cbc is None:
            convergence = False # first iteration, convergence is False to repeat
        else:
            convergence = ((df_cbc-old_df_cbc).abs().max() <= CONVERGENCE_THRESH).any()
        return convergence,df_cbc

    def run_new(self, n=1000, add_time_uncertainty=True, add_lvo_uncertainty=True,
            fix_performance=False):
        """Run the model, determine num of simulation by convergence"""
        costs.Costs.inflate(2016)
        convergence = False

        n_sim = 5000
        NRUN_MAX=20
        old_df_cbc = None
        for c in range(NRUN_MAX):
            ais_times = times.IschemicTimes(self._patient, self.hospitals, n_sim,
                                            add_time_uncertainty,
                                            add_lvo_uncertainty,
                                            fix_performance)
            ais_model = ais_outcomes.IschemicModel(ais_times)
            outcomes = ais_model.run_all_strategies()
            markov = cohort.Population(self._patient, outcomes)
            markov.analyze()
            markov_results = results.Results(markov)
            convergence,df_cbc = self._check_convergence(markov_results,n_sim,old_df_cbc)
            n_sim += 1000*(c+1)
            old_df_cbc = df_cbc
            if convergence:
                break
            else:
                print(f'repeating for nsim of {n_sim}')
        return markov_results,markov,ais_times
