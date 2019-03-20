from pathlib import Path
from itertools import chain

import trueskill as ts

INITIAL_PLAYERS_LIST = Path("./players.list")

ts.setup(mu=25.0, sigma=8.333333333333334, beta=4.166666666666667, tau=0.08333333333333334, draw_probability=0.001)


def create_state():
    return {}


def infer_weight(score_a, score_b):
    if score_a == score_b:
        return None
    if max(score_a, score_b) == 5:
        return 0.5
    if max(score_a, score_b) == 10:
        return 1
    return None


def game_played(state, team_a, team_b, score_a, score_b):
    ranking = [0, 0]

    # if played until 5 then weight game to half
    w = infer_weight(score_a, score_b)

    if score_a > score_b:
        ranking = [0, 1]
    elif score_a < score_b:
        ranking = [1, 0]

    ta = {p: state[p] for p in team_a}
    tb = {p: state[p] for p in team_b}

    weights = [[w for _ in range(len(ta))],
               [w for _ in range(len(ta))]]

    new_ta, new_tb = ts.rate([ta, tb], ranks=ranking, weights=weights)
    for p, r in chain(new_ta.items(), new_tb.items()):
        state[p] = r

    return state


def calc_leaderboard(state):
    return [(p, ts.expose(r)) for p, r in state.items()]


def add_player_(state, player: str):
    """works inplace"""
    assert ' ' not in player

    assert player not in state
    state[player] = ts.Rating()
