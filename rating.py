import itertools
import math

import trueskill
from trueskill import Rating, quality_1vs1, rate_1vs1, rate


ts = trueskill.TrueSkill(mu=25.0,
                         sigma=8.333333333333334,
                         beta=4.166666666666667,
                         tau=0.08333333333333334,
                         draw_probability=0.0,
                         backend=None)


def win_probability(team1, team2, ts_env=None):
    beta = ts_env.beta if ts_env is not None else trueskill.BETA
    delta_mu = sum(r.mu for r in team1) - sum(r.mu for r in team2)
    sum_sigma = sum(r.sigma ** 2 for r in itertools.chain(team1, team2))
    size = len(team1) + len(team2)
    denom = math.sqrt(size * (beta * beta) + sum_sigma)
    ts = trueskill.global_env()
    return ts.cdf(delta_mu / denom)



alice, bob = ts.create_rating(50, 25/3), Rating(24, 25/3)  # assign Alice and Bob's ratings

if quality_1vs1(alice, bob) < 0.50:
    print('This match seems to be not so fair')

alice, bob = rate_1vs1(alice, bob)

win_probability([alice], [bob])



res = rate([[alice, alice], [bob]], ranks=[1, 0])



