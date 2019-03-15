from pathlib import Path
from itertools import chain

import trueskill as ts

INITIAL_PLAYERS_LIST = Path("./players.list")

LEAGUE_5 = "Short league"
LEAGUE_10 = "Long league"

ts.setup(mu=25.0, sigma=8.333333333333334, beta=4.166666666666667, tau=0.08333333333333334, draw_probability=0.001)


def create_state():
    state = {}
    for league in [LEAGUE_5, LEAGUE_10]:
        state[league] = {p.strip(): ts.Rating() for p in INITIAL_PLAYERS_LIST.read_text().splitlines() if p.strip()}
    return state


def infer_league(score_a, score_b):
    if score_a == score_b:
        return None
    if max(score_a, score_b) == 5:
        return LEAGUE_5
    if max(score_a, score_b) == 10:
        return LEAGUE_10
    return None


def game_played(state, team_a, team_b, score_a, score_b):
    ranking = [0, 0]

    league = infer_league(score_a, score_b)
    if league is None:
        raise RuntimeError('Unknown league')

    if score_a > score_b:
        ranking = [0, 1]
    elif score_a < score_b:
        ranking = [1, 0]

    ta = {p: state[league][p] for p in team_a}
    tb = {p: state[league][p] for p in team_b}

    new_ta, new_tb = ts.rate([ta, tb], ranks=ranking)
    for p, r in chain(new_ta.items(), new_tb.items()):
        state[league][p] = r

    return state


def calc_leaderboard(state):
    return [(p, ts.expose(r)) for p, r in state.items()]


def add_player(state, player: str):
    """works inplace"""
    assert ' ' not in player
    for league in [LEAGUE_5, LEAGUE_10]:
        assert player not in league
        state[league][player] = ts.Rating()
