"""Flexible characterization of stroke severity."""
import abc
import numpy as np


class Severity(abc.ABC):
    """
    Abstract class defining the methods required for any characterization
        of stroke severity.
    """

    @abc.abstractmethod
    def prob_LVO_given_AIS(self, n=1, add_uncertainty=False):
        """
        Get the probability of an LVO under the assumption that the severity
            describes an acute ischemic stroke.
        """
        pass

    @abc.abstractmethod
    def get_NIHSS(self):
        """
        Get the NIHSS score equivalent to this stroke severity.
        """
        pass


class RACE(Severity):
    """Severity represented by the RACE score."""

    def __init__(self, score):
        if score < 0 or score > 9:
            raise ValueError(f'Invalid RACE score {score}')
        self.score

    def prob_LVO_given_AIS(self, n=1, add_uncertainty=False):
        """
        Get the probability of an LVO under the assumption that the severity
            describes an acute ischemic stroke.
        """
        # Perez de la Ossa et al. Stroke 2014 data for p lvo given ais
        def p_lvo_logistic_helper(b0, b1):
            return (1.0 / (1.0 + np.exp(-b0 - b1 * self.score)))

        if not add_uncertainty:
            p_lvo = np.repeat(p_lvo_logistic_helper(-2.9297, 0.5533), n)
        else:
            lower = p_lvo_logistic_helper(-3.6526, 0.4141)
            upper = p_lvo_logistic_helper(-2.2067, 0.6925)
            p_lvo = np.random.uniform(lower, upper, n)

        return p_lvo

    def get_NIHSS(self):
        """
        Get the NIHSS score equivalent to this stroke severity.
        Perez de la Ossa et al. Stroke 2014, Schlemm analysis
        """
        if self.score == 0:
            nihss = 1
        else:
            nihss = -0.39 + 2.39 * self.score
        return nihss


class NIHSS(Severity):
    """
    Severity represented by NIHSS score, with LVO probability computed by
        converting to RACE.
    """

    def __init__(self, score):
        if score < 0 or score > 42:
            raise ValueError(f'Invalid NIHSS score {score}')
        self.score = score
        self._get_RACE()

    def _get_RACE(self):
        if self.score <= 1:
            race = 0
        else:
            race = (self.score + 0.39) / 2.39
        self._RACE = RACE(race)

    def prob_LVO_given_AIS(self, n=1, add_uncertainty=False):
        """
        Get the probability of an LVO under the assumption that the severity
            describes an acute ischemic stroke. Computed by converting to a
            RACE score first via linear regression.
        """
        return self._RACE.prob_LVO_given_AIS(n, add_uncertainty)

    def get_NIHSS(self):
        """
        Get the NIHSS score
        """
        return self.score
