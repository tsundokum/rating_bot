`@kicker_rating_bot`
register a game, log to a file, alter ranks

Syntax:
```
game: team "vs"i team scores
team: player [player]
player: /\w+/
scores: score+
score: NUMBER ":" NUMBER
```

Examples:
```
@kicker_rating_bot alice vs bob 10:9 10:8 1:10
@kicker_rating_bot alice bob vs charles dave 0:5
```
"Logged game ..." message confirms that message was registered.

First player is a goalkeeper.

`/ranks`
print ranks table



`/cancel`
Cancel last registered games. Works only once!

`/db`
Download database file with games and cancels in jsonlines format.
The file is sent by private message, so if bot can't write you, perhaps you should PM first

`/new_player \w+`