# TODO register games only in a group or log to the gruop
# TODO log all messages to a file
# TODO cancel last record

from pathlib import Path
from random import randint
import pickle
import os
import threading
from pprint import pprint
import sys
import traceback
import logging

import telegram
from telegram import InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, InlineQueryHandler

from logic import create_state, game_played, calc_leaderboard, infer_league, LEAGUE_10, LEAGUE_5
from parser import game_parser


# logging.getLogger('message_logger').addHandler(logging.FileHandler('messages.log'))
logging.basicConfig(filename="games.log", level=logging.INFO, format="%(asctime)s\t%(message)s")
logging.getLogger('games_logger').addHandler(logging.FileHandler('games.log'))

token = Path("~/.kicker_bot").expanduser().read_text().strip()

STATE_PICKLE = Path("./state.pickle")
if os.path.isfile(STATE_PICKLE):
    print(f"Loading state from {STATE_PICKLE}")
    with STATE_PICKLE.open("rb") as f:
        ranks = pickle.load(f)
else:
    print("Creating a new state")
    ranks = create_state()

bot = telegram.Bot(token=token)
print(bot.get_me())

updater = Updater(token=token)
dispatcher = updater.dispatcher


def on_start(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="Hello, kicker player!")


start_handler = CommandHandler('start', on_start)
dispatcher.add_handler(start_handler)


def on_ranks(bot, update):
    rp = calc_leaderboard(ranks)
    leaderboard = '\n'.join(f"{r:.0f} {p}" for p, r in sorted(rp, key=lambda x: x[1], reverse=True))
    bot.send_message(chat_id=update.message.chat_id, text=leaderboard)


ranks_handler = CommandHandler('ranks', on_ranks)
dispatcher.add_handler(ranks_handler)


def register_game(bot, update, game_str):
    global ranks
    g = game_parser.parse(game_str)
    if len(g) < 3 or len(g[2][-1]) != 2:
        bot.send_message(chat_id=update.message.chat_id,
                         text=f'example: player_a1 player_a2 vs player_b1 player_b2 5:10 3:5')
    else:
        for p in g[0] + g[1]:
            if p not in ranks[LEAGUE_5]:
                bot.send_message(chat_id=update.message.chat_id,
                                 text=f"Player {p} is not registered")
                return

        for score in g[2]:
            league = infer_league(*score)
            if league is None:
                bot.send_message(chat_id=update.message.chat_id,
                                 text=f"Unknow league for score {score[0]}:{score[1]}")
                continue
            bot.send_message(chat_id=update.message.chat_id,
                             text=f"Logged1 game: {' and '.join(g[0])} ({score[0]}) VS {' and '.join(g[1])} ({score[1]})")
            logging.info(pickle.dumps({"team_1": g[0],
                                       "team_2": g[1],
                                       "score_1": score[0],
                                       "score_2": score[1],
                                       "message_id": update.message.message_id,
                                       "from": update.message.from_user.to_dict}))
            ranks = game_played(ranks, g[0], g[1], score[0], score[1])
            # bot.send_message(chat_id=update.message.chat_id, text=f'New ranks: {ranks}')
        with STATE_PICKLE.open("wb") as f:
            pickle.dump(ranks, f)


def on_log_game(bot, update):
    t = update.message.text
    assert t.startswith("/game ")
    t = t[len("/game"):].strip()
    register_game(bot, update, t)


game_handler = CommandHandler('game', on_log_game)
dispatcher.add_handler(game_handler)


def create_game_structure(game_state):
    team1 = ['unknown']
    team2 = ['unknown']
    scores = [['?', '?']]

    if len(game_state) >= 1:
        team1 = game_state[0]
    if len(game_state) >= 2:
        team2 = game_state[1]
    if len(game_state) == 3:
        scores = []
        for s in game_state[2]:
            score = ['?', '?']
            score[0] = s[0]
            if len(s) == 2:
                score[1] = s[1]
            scores.append(score)

    team1_members = ' & '.join(p + ("" if p in ranks[LEAGUE_5] else "(???)") for p in team1)
    team2_members = '&'.join(p + ("" if p in ranks[LEAGUE_5] else "(???)") for p in team2)
    t = f"{team1_members} VS {team2_members} Score is {{}}:{{}} ({{}})"

    res = []
    for s in scores:
        league = infer_league(*s)
        if league is None:
            league = "Uknown League"
        res.append(t.format(*s, league))

    return res


def on_message(bot, update):
    text = update.message.text
    # logging.getLogger("message_logger").info(update)
    if text.startswith("@kicker_rating_bot"):
        s = text[len("@kicker_rating_bot"):].strip()
        try:
            register_game(bot, update, s)
        except Exception as ex:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_exception(exc_type, exc_value, exc_traceback,
                                      limit=5, file=sys.stdout)


message_handler = MessageHandler(Filters.text, on_message)
dispatcher.add_handler(message_handler)


def inline_caps(bot, update):
    try:
        print("inline_caps called")
        query = update.inline_query.query.strip()
        if query:
            game = game_parser.parse(query)
        else:
            game = []
        print(f"game_state={game}")

        gs = create_game_structure(game)
        results = list()
        for i, t in enumerate(gs):
            results.append(
                InlineQueryResultArticle(
                    id=randint(0, 1e12),
                    title=t,
                    input_message_content=InputTextMessageContent(t)
                )
            )
        bot.answer_inline_query(update.inline_query.id, results)
    except Exception as ex:
        print(ex)


inline_caps_handler = InlineQueryHandler(inline_caps)
dispatcher.add_handler(inline_caps_handler)


def shutdown():
    updater.stop()
    updater.is_idle = False


def stop(bot, update):
    threading.Thread(target=shutdown).start()


stop_handler = CommandHandler('stop', stop)
updater.dispatcher.add_handler(stop_handler)


print('Polling started... (interrupt to exit)')
try:
    updater.start_polling()
except KeyboardInterrupt:
    print("Stopping")
    updater.stop()
    print(f"Saving current state to {STATE_PICKLE}")
    with STATE_PICKLE.open("wb") as f:
        pickle.dump(ranks, f)
