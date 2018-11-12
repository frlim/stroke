"""Flexible characterization of stroke severity."""
import abc
import numpy as np
import constants


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

    @property
    @abc.abstractmethod
    def NIHSS(self):
        """
        Get the NIHSS score equivalent to this stroke severity.
        """
        pass

    def p_good_outcome_post_evt_success(self, time_onset_reperfusion):
        '''
        Saver et al. JAMA 2016, Schlemm analysis
        Note: had to redo the regression
        '''
        beta = (-0.00879544 - 9.01419716e-05 * time_onset_reperfusion)
        return np.exp(beta * self.NIHSS)

    def p_good_outcome_no_reperfusion(self):
        '''
        Schlemm, used a few different sources for points on the piecewise
        linear regression (3 distinct points: 0.05 at NIHSS 20, 1 at NIHSS 0,
        and 0.3 at for an NIHSS at 16)
        '''
        if self.NIHSS >= 20:
            return 0.05
        else:
            return (-0.0464 * self.NIHSS) + 1.0071

    def p_good_outcome_ais_no_lvo(self, time_onset_tpa):
        '''
        * Note that if your time from onset to tPA is > 270, you won't
            actually get tPA.
        Schelmm analysis, extracted from a few sources and assumed that
        there is interaction between treatment effect of thrombolysis and
        stroke severity
        Didn't have data for odds ratio with time for patients without LVO,
        but there is no consistent evidence that it differs for patients
        with and without LVO
        '''
        baseline_prob = 0.001 * self.NIHSS**2 - 0.0615 * self.NIHSS + 1

        odds_ratio = -0.0031 * time_onset_tpa + 2.068
        # if baseline_prob == 1.0:
        #     baseline_prob = 0.999999999999
        baseline_prob_to_odds = baseline_prob / (1 - baseline_prob)
        new_odds = baseline_prob_to_odds * odds_ratio
        adjusted_prob = new_odds / (1 + new_odds)

        return np.where(time_onset_tpa < constants.time_limit_tpa,
                        adjusted_prob, baseline_prob)

    def p_reperfusion_endovascular(self):
        # Saver et al. JAMA 2016, Schlemm analysis
        return 0.71

    def p_early_reperfusion_thrombolysis(self, time_to_groin):
        return 0.18 * np.minimum(70, time_to_groin) / 70


class RACE(Severity):
    """Severity represented by the RACE score."""

    @property
    def NIHSS(self):
        return self._NIHSS

    @property
    def score(self):
        return self._score

    @score.setter
    def set_score(self, score):
        if score < 0 or score > 9:
            raise ValueError(f'Invalid RACE score {score}')
        self._score = score
        self._NIHSS = self._get_NIHSS()

    def __init__(self, score):
        self.score = score

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

    def _get_NIHSS(self):
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

    @property
    def NIHSS(self):
        return self.score

    @property
    def score(self):
        return self._score

    @score.setter
    def set_score(self, score):
        if score < 0 or score > 42:
            raise ValueError(f'Invalid NIHSS score {score}')
        self.score = score
        self._get_RACE()

    def __init__(self, score):
        self.score = score

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
