"""
Aggregate model runs and determine optimal strategies
"""
import functools
import warnings
from collections import Counter
import numpy as np

@functools.total_ordering
class FormattedResult:
    """
    Store results from a single model run for purposes of determining the
        optimal strategy for that run.
    """

    def __init__(self, strategy, qaly, cost, icer):
        self.strategy = strategy
        self.qaly = qaly
        self.cost = cost
        self.icer = icer

    def __eq__(self, other):
        return ((self.strategy, self.qaly, self.cost, self.icer) ==
                (other.strategy, other.qaly, other.cost, other.icer))

    def __lt__(self, other):
        """
        Sort order to be used in determining optimal results, by qaly, then
            by cost, then by strategy.
        """
        return ((self.qaly, self.cost, self.strategy) <
                (other.qaly, other.cost, other.strategy))

    def equivalent(self, other):
        """Test for equivalently good strategies"""
        return (self.qaly, self.cost) == (other.qaly, other.cost)


class Results:
    """
    Tabulated results, with counts of how often each strategy provides the
        maximum benefit and is optimal when considering cost
    """
    @property
    def max_qaly_counts(self):
        return self._max_qaly_counts

    @property
    def optimal_counts(self):
        return self._optimal_counts

    @property
    def threshold(self):
        return self._threshold

    def __init__(self, cohort, threshold_ICER=100000):
        """
        Generate results from analyzed markov cohort for all strategies
        """
        # Record counts of maximum QALY strategies
        max_qalys = Counter()
        for max_qaly_index in cohort.qalys.argmax(axis=1):
            max_qalys[cohort.strategies[max_qaly_index]] += 1
        self._max_qaly_counts = max_qalys

        # Record counts of optimal strategies considering cost
        optimal_counts = Counter()
        for j, strategy in enumerate(cohort.strategies):
            # listed in all possible strategies as 0 first
            # to help differentiate from centers that are not
            # a feasible option (too far away to even consider) in final results
            optimal_counts[strategy] = 0
        for i in range(cohort.qalys.shape[0]):
            data = []
            for j, strategy in enumerate(cohort.strategies):
                qaly = cohort.qalys[i, j]
                cost = cohort.costs[i, j]
                if np.isnan(qaly) or np.isnan(cost):
                    continue
                data.append(FormattedResult(strategy, qaly, cost, None))
            optimal = get_optimal(data, threshold_ICER)
            if optimal: optimal_counts[optimal] += 1
        self._optimal_counts = optimal_counts
        self._threshold = threshold_ICER

    @property
    def counts_by_center(self):
        counts_by_center = {}
        for strategy, count in self._optimal_counts.items():
            center = strategy.center
            if center in counts_by_center:
                counts_by_center[center] += count
            else:
                counts_by_center[center] = count
        return counts_by_center

    @property
    def percentages_by_center(self):
        cbc = self.counts_by_center
        total = sum(cbc.values())
        return {center: count / total for center, count in cbc.items()}

    @property
    def optimal_destination(self):
        cbc = self.counts_by_center
        if cbc is not None:
            return max(cbc, key=lambda center: cbc[center])
        else:
            pbc = self.percentages_by_center
            return max(cbc, key=lambda center: pbc[center])

    @property
    def optimal_strategy(self):
        cbs = self._optimal_counts
        if cbs is not None:
            return max(cbs, key=lambda center: cbs[center])


def get_optimal(data, threshold):
    """
    Given a list of FormattedResults representing strategies for a single
        model run, select the optimal result and return it.
    """
    if len(data) == 0: return None # if empty list returns None
    sort_and_remove_duplicates(data)

    # Then, iteratively go through dataframe dropping strategies that are
    # dominated; i.e. strategies where the y value is lower than the one
    # before it (we already know that the x value is higher)

    while True:
        end = False
        for index in range(len(data)):
            if index == len(data) - 1:
                end = True
                break
            else:
                this = data[index]
                next_ = data[index + 1]
                if (this.qaly >= next_.qaly and this.cost < next_.cost):
                    # Del instead of pop because we don't care what was
                    #   deleted
                    del data[index + 1]
                    # Restart from the top
                    break
        if end is True:
            break

    if len(data) <= 1:
        return data[0].strategy

    # Now comes a tricky part. We calculate ICERs between adjacent pairs
    # and drop the strategies where the ICER is greater than the next pair
    while True:
        end = False
        icers = get_icers(data)
        # length of ICER's is 1 less than the length of data
        for index in range(len(icers)):
            if index == len(icers) - 1:
                end = True
                break
            else:
                if icers[index] > icers[index + 1]:
                    # Del instead of pop because we don't care what was
                    #   deleted
                    # This is a little tricky, but assume we have icers
                    # like this:
                    # 2 vs 1 -> 100
                    # 3 vs 2 -> 300
                    # 4 vs 3 --> 200
                    # Then because 3 vs 2 is greater than 4 vs 3, we delete
                    # the third strategy which is index 1 in our ICERs BUT
                    #   is actually index 2 in our data
                    del data[index + 1]
                    # Restart from the top
                    break
        if end is True:
            # Append ICER's
            for i in range(1, len(data)):
                data[i].icer = icers[i - 1]
            break

    for this_data in reversed(data):
        if this_data.icer is None:
            return this_data.strategy
        elif this_data.icer < threshold:
            return this_data.strategy


def sort_and_remove_duplicates(data):
    # sort inplace by the defined ordering on FormattedResults
    data.sort()

    # Remove strategies with identical cost and qaly values, keeping the first
    #   of each according to the ordering on FormattedResults
    duplicates = []
    for i, element in enumerate(data):
        if i == 0:
            continue
        prev = data[i - 1]
        if prev.equivalent(element):
            duplicates.append(i)
    while duplicates:
        # Remove duplicates in reverse order
        index_to_remove = duplicates.pop()
        # print(f'Removing {index_to_remove}')
        del data[index_to_remove]


def get_icers(data):
    icers = []
    for i in range(1, len(data)):
        num = data[i].cost - data[i - 1].cost
        den = data[i].qaly - data[i - 1].qaly
        if num == 0.0 and den == 0.0:
            raise ValueError('Identical strategies not caught')
            icer = 0
        elif den == 0.0:
            warnings.warn("Two strategies with exactly equal benefit")
            icer = np.sign(num) * np.Inf
        else:
            icer = num / den
        icers.append(icer)
    return icers
