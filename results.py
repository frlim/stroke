"""
Aggregate model runs and determine optimal strategies
"""
from collections import Counter


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
        for i in range(cohort.qalys.shape[0]):
            data = []
            for j, strategy in enumerate(cohort.strategies):
                data.append(FormattedResult(strategy,
                                            cohort.qalys[i, j],
                                            cohort.costs[i, j],
                                            None))
            optimal = get_optimal(data, threshold_ICER)
            optimal_counts[optimal] += 1
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


def get_optimal(data, threshold):
    """
    Given a list of FormattedResults representing strategies for a single
        model run, select the optimal result and return it.
    """
    # sort inplace by the y and x values
    data.sort(key=lambda x: (x.qaly, x.cost))

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


def get_icers(data):
    icers = []
    for i in range(1, len(data)):
        num = data[i].cost - data[i - 1].cost
        den = data[i].qaly - data[i - 1].qaly
        icers.append(num / den)
    return icers
