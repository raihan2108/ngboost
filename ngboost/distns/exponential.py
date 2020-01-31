import scipy as sp
import numpy as np
from scipy.stats import expon as dist
from ngboost.distns import RegressionDistn
from ngboost.scores import LogScore, CRPScore

eps = 1e-10


class ExponentialLogScore(LogScore):

    def score(self, Y):
        E, T = Y["Event"], Y["Time"]
        cens = (1-E) * np.log(1 - self.dist.cdf(T) + eps)
        uncens = E * self.dist.logpdf(T)
        return -(cens + uncens)
    
    def d_score(self, Y):
        E, T = Y["Event"], Y["Time"]
        cens = (1-E) * T.squeeze() / self.scale
        uncens = E * (-1 + T.squeeze() / self.scale)
        return -(cens + uncens).reshape((-1, 1))

    def metric(self):
        FI = np.ones_like(self.scale)
        return FI[:, np.newaxis, np.newaxis]

class ExponentialCRPScore(CRPScore):
    
    def score(self, Y):
        E, T = Y["Event"], Y["Time"]
        score = T + self.scale * (2 * np.exp(-T / self.scale) - 1.5)
        score[E == 1] -= 0.5 * self.scale[E == 1] * np.exp(-2 * T[E == 1] / self.scale[E == 1])
        return score

    def d_score(self, Y):
        E, T = Y["Event"], Y["Time"]
        deriv = 2 * np.exp(-T / self.scale) * (self.scale + T) - 1.5 * self.scale
        deriv[E == 1] -= np.exp(-2 * T[E == 1] / self.scale[E == 1]) * \
                         (0.5 * self.scale[E == 1] - T[E == 1])
        return deriv.reshape((-1, 1))

    def metric(self):
        M = 0.5 * self.scale[:, np.newaxis, np.newaxis]
        return M

class Exponential(RegressionDistn):

    n_params = 1
    censored_scores = [ExponentialLogScore, ExponentialCRPScore]

    def __init__(self, params):
        self._params = params
        self.scale = np.exp(params[0])
        self.dist = dist(scale=self.scale)
    
    def __getattr__(self, name): 
        if name in dir(self.dist):
            return getattr(self.dist, name)
        return None
    
    # should implmenent a `sample()` method

    @property
    def params(self):
        return {'scale':self.scale}

    def fit(Y):
        m, s = sp.stats.expon.fit(Y)
        return np.array([np.log(m + s)])

