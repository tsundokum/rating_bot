# TODO beatifull ranks table
# TODO print last games
# TODO fails when many games logged at once
# TODO better help -- proper games syntax: team game and single game
# TODO autopin best players

from pathlib import Path
from random import randint
import pickle
import os
import threading
from pprint import pprint
import sys
import traceback
import logging
import copy
import json

import telegram
from telegram import InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, InlineQueryHandler

from logic import create_state, game_played, calc_leaderboard, add_player_
from parser import game_parser

SEASON = "season_6"

# logging.getLogger('message_logger').addHandler(logging.FileHandler('messages.log'))
logging.basicConfig(filename=f"{SEASON}.log", level=logging.INFO, format="%(asctime)s\t%(message)s")

token = Path("~/.kicker_bot").expanduser().read_text().strip()



ALLOWED_CHATS = {-1001284542064}
GAMES_LOG_FN = f"{SEASON}.jl"
HELP_MESSAGE_FN = "help.md"

STATE_PICKLE = Path(f"./{SEASON}.state.pickle")
if os.path.isfile(STATE_PICKLE):
    print(f"Loading state from {STATE_PICKLE}")
    with STATE_PICKLE.open("rb") as f:
        ranks = pickle.load(f)
else:
    print("Creating a new state")
    ranks = create_state()
prev_ranks = None
last_games_added_count = 0

bot = telegram.Bot(token=token)
print(bot.get_me())

updater = Updater(token=token)
dispatcher = updater.dispatcher


def log_db(dict_log: dict):
    s = json.dumps(dict_log)
    with open(GAMES_LOG_FN, "a") as f:
        print(s, file=f)


def on_start(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="Hello, kicker player!")


start_handler = CommandHandler('start', on_start)
dispatcher.add_handler(start_handler)


def on_help(bot, update):
    with open(HELP_MESSAGE_FN) as f:
        t = f.read()
    bot.send_message(chat_id=update.message.from_user.id, text=t, parse_mode=telegram.ParseMode.MARKDOWN)


help_handler = CommandHandler('help', on_help)
dispatcher.add_handler(help_handler)


def on_download_db(bot, update):
    bot.send_document(chat_id=update.message.from_user.id, document=open(GAMES_LOG_FN, "rb"))


db_handler = CommandHandler('db', on_download_db)
dispatcher.add_handler(db_handler)


def on_ranks(bot, update):
    rp = calc_leaderboard(ranks)
    leaderboard = '\n'.join(f"{r:.1f} {p}" for p, r in sorted(rp, key=lambda x: x[1], reverse=True))
    bot.send_message(chat_id=update.message.chat_id, text=leaderboard)


ranks_handler = CommandHandler('ranks', on_ranks)
dispatcher.add_handler(ranks_handler)


def register_game(bot, update, game_str):
    global ranks, prev_ranks, last_games_added_count
    if update.message.chat_id not in ALLOWED_CHATS:
        bot.send_message(chat_id=update.message.chat_id,
                         text=f"Can register games only in official chat 'Kicker Federation'")
        return

    g = game_parser.parse(game_str)
    if len(g) < 3 or len(g[2][-1]) != 2:
        bot.send_message(chat_id=update.message.chat_id,
                         text=f'example: player_a1 player_a2 vs player_b1 player_b2 5:10 3:5')
    else:
        for p in g[0] + g[1]:
            if p not in ranks:
                bot.send_message(chat_id=update.message.chat_id,
                                 text=f"Player {p} is not registered")
                return

        prev_ranks_ = copy.deepcopy(ranks)
        games_added_count = 0
        for score in g[2]:
            if max(*score) in (5, 10) and score[0] != score[1] is None:
                bot.send_message(chat_id=update.message.chat_id,
                                 text=f"We play until 5 or 10, score must not equal")
                continue
            bot.send_message(chat_id=update.message.chat_id,
                             text=f"Logged game: {' and '.join(g[0])} ({score[0]}) VS {' and '.join(g[1])} ({score[1]})")
            log_db({"time": update.message.date.isoformat(),
                    "type": "log_game",
                    "team_1": g[0],
                    "team_2": g[1],
                    "score_1": score[0],
                    "score_2": score[1],
                    "message_id": update.message.message_id,
                    "from": update.message.from_user.to_dict(),
                    "message": update.message.to_dict()})
            ranks = game_played(ranks, g[0], g[1], score[0], score[1])
            games_added_count += 1

        if games_added_count > 0:
            prev_ranks = prev_ranks_
            last_games_added_count = games_added_count
            with STATE_PICKLE.open("wb") as f:
                pickle.dump(ranks, f)


def on_cancel(bot, update):
    global ranks, prev_ranks, last_games_added_count
    if not last_games_added_count:
        bot.send_message(chat_id=update.message.chat_id, text="Can't cancel")
    else:
        ranks = prev_ranks
        log_db({"time": update.message.date.isoformat(),
                "type": "cancel",
                "count": last_games_added_count,
                "message_id": update.message.message_id,
                "from": update.message.from_user.to_dict()})
        with STATE_PICKLE.open("wb") as f:
            pickle.dump(ranks, f)

        bot.send_message(chat_id=update.message.chat_id, text=f"Last {last_games_added_count} game(s) canceled")
        prev_ranks = None
        last_games_added_count = 0


cancle_handler = CommandHandler('cancel', on_cancel)
dispatcher.add_handler(cancle_handler)


def on_add_new_players(bot, update):
    global ranks, prev_ranks, last_games_added_count

    t = update.message.text
    assert t.startswith("/new_player ")

    if update.message.chat_id not in ALLOWED_CHATS:
        bot.send_message(chat_id=update.message.chat_id,
                         text=f"Can register a new player only in official chat 'Kicker Federation'")
        return

    new_player = t[len("/new_player"):].strip()
    add_player_(ranks, new_player)
    bot.send_message(chat_id=update.message.chat_id,
                     text=f"Registered a new player '{new_player}'")

    with STATE_PICKLE.open("wb") as f:
        pickle.dump(ranks, f)

    last_games_added_count = 0


new_player_handler = CommandHandler('new_player', on_add_new_players)
dispatcher.add_handler(new_player_handler)


# def on_log_game(bot, update):
#     t = update.message.text
#     assert t.startswith("/game ")
#     t = t[len("/game"):].strip()
#     register_game(bot, update, t)
#
#
# game_handler = CommandHandler('game', on_log_game)
# dispatcher.add_handler(game_handler)


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

    team1_members = ' & '.join(p + ("" if p in ranks else "(???)") for p in team1)
    team2_members = '&'.join(p + ("" if p in ranks else "(???)") for p in team2)
    t = f"{team1_members} VS {team2_members} Score is {{}}:{{}}"

    res = []
    for s in scores:
        res.append(t.format(*s))

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


# def inline_caps(bot, update):
#     try:
#         print("inline_caps called")
#         query = update.inline_query.query.strip()
#         if query:
#             game = game_parser.parse(query)
#         else:
#             game = []
#         print(f"game_state={game}")
#
#         gs = create_game_structure(game)
#         results = list()
#         for i, t in enumerate(gs):
#             results.append(
#                 InlineQueryResultArticle(
#                     id=randint(0, 1e12),
#                     title=t,
#                     input_message_content=InputTextMessageContent(t)
#                 )
#             )
#         bot.answer_inline_query(update.inline_query.id, results)
#     except Exception as ex:
#         print(ex)
#
#
# inline_caps_handler = InlineQueryHandler(inline_caps)
# dispatcher.add_handler(inline_caps_handler)


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
