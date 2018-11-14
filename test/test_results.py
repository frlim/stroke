import unittest
from stroke import results, strategy
from . import helper


class ResultTestCase(unittest.TestCase):
    '''Tests for processing a set of model results.'''

    def setUp(self):
        """
        Generate a set of centers and strategies to incorporate in
            results testing.
        """
        primaries, comprehensives = helper.get_centers()
        self.primaries = primaries
        self.comprehensives = comprehensives
        self.prim_strats = [strategy.Strategy.primary(x) for x in primaries]
        self.drip_strats = [strategy.Strategy.drip_and_ship(x)
                            for x in primaries]
        self.comp_strats = [strategy.Strategy.comprehensive(x)
                            for x in comprehensives]

    def test_equivalent(self):
        """Test that two equivalent results are recognized as such"""
        qaly = 14.1
        cost = 60000.5
        strat1 = self.drip_strats[0]
        res1 = results.FormattedResult(strat1, qaly, cost, None)
        strat2 = self.comp_strats[0]
        res2 = results.FormattedResult(strat2, qaly, cost, None)

        self.assertTrue(res1.equivalent(res2))

    def test_nonequivalent(self):
        """Test that two nonequivalent results are recognized as such"""
        qaly = 14.1
        cost = 60000.5
        strat1 = self.drip_strats[0]
        res1 = results.FormattedResult(strat1, qaly, cost, None)
        strat2 = self.comp_strats[0]
        res2 = results.FormattedResult(strat2, qaly, cost + 1, None)

        self.assertFalse(res1.equivalent(res2))

    def test_order_nonequivalent(self):
        """Test that two nonequivalent results are ordered correctly"""
        qaly = 14.1
        cost = 60000.5
        strat1 = self.drip_strats[0]
        res1 = results.FormattedResult(strat1, qaly, cost, None)
        strat2 = self.comp_strats[0]
        res2 = results.FormattedResult(strat2, qaly, cost + 1, None)

        self.assertGreater(res2, res1)

    def test_order_equivalent_time(self):
        """Test that two equivalent results are ordered correctly by time"""
        qaly = 14.1
        cost = 60000.5
        strat1 = self.drip_strats[0]
        strat1.center.time = 30
        res1 = results.FormattedResult(strat1, qaly, cost, None)
        strat2 = self.comp_strats[0]
        strat2.center.time = 20
        res2 = results.FormattedResult(strat2, qaly, cost, None)

        self.assertLess(res2, res1)

    def test_order_equivalent_kind(self):
        """Test that two equivalent results are ordered correctly by kind"""
        qaly = 14.1
        cost = 60000.5
        strat1 = self.drip_strats[0]
        strat1.center.time = 30
        res1 = results.FormattedResult(strat1, qaly, cost, None)
        strat2 = self.comp_strats[0]
        strat2.center.time = 30
        res2 = results.FormattedResult(strat2, qaly, cost, None)

        self.assertLess(res2, res1)
