`/ranks`
print ranks table

`@kicker_rating_bot`
register a game, log to a file, alter ranks
game syntax:
```game:     team
        | team "vs"i
        | team "vs"i team
        | team "vs"i team scores
team: (player)+
player: /\w+/
scores: score+
score: NUMBER COLON NUMBER?
COLON: ":"
```

Examples:
```
@kicker_rating_bot alice vs bob 10:9 10:8 1:10
@kicker_rating_bot alice bob vs charles dave 0:5
```

"Logged game ..." message confirms that message was registered

`/cancel`
Cancel last registered games. Works only once!

`/db`
Download database file with games and cancels in jsonlines format.
The file is sent by private message, so if bot can't write you, perhaps you should PM first