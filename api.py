from pathlib import Path
from parser import game_parser
from random import randint

import telegram
from telegram import InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, InlineQueryHandler


token = Path("~/.kicker_bot").expanduser().read_text().strip()

bot = telegram.Bot(token=token)
print(bot.get_me())

updater = Updater(token=token)
dispatcher = updater.dispatcher


def on_start(bot, update):
    print('on_start called')
    bot.send_message(chat_id=update.message.chat_id, text="Hello, kicker player!")


def on_message(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text=f'Received a message "{update}"')


start_handler = CommandHandler('start', on_start)
dispatcher.add_handler(start_handler)

message_handler = MessageHandler(Filters.text, on_message)
dispatcher.add_handler(message_handler)


registered_players = 'marat liza ilya nadya zhamal vadim pasha lev roma gleb'.split()


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

    t = f"{' & '.join(team1)} {{}} Vs {'&'.join(team2)} {{}}"
    return [t.format(*s) for s in scores]


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


print('Polling started... (interrupt to exit)')
try:
    updater.start_polling()
except KeyboardInterrupt:
    updater.stop()
