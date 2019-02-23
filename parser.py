from lark import Lark, Transformer, v_args

game_grammar = """
    game: team 
        | team "vs"i 
        | team "vs"i team 
        | team "vs"i team scores
    team: (player)+
    player: /\w+/
    scores: score+ 
    score: NUMBER COLON NUMBER?
    
    COLON: ":"
    %import common.NUMBER
    %import common.WS
    %ignore WS
"""


class GameTransformer(Transformer):
    def team(self, players):
        return players

    def player(self, p):
        return str(p[0])

    def score(self, s):
        if len(s) == 3:
            return [int(s[0]), int(s[2])]
        if len(s) < 3:
            return [int(s[0])]

    def scores(self, ss):
        return ss

    def game(self, args):
        return args

game_parser = Lark(game_grammar, parser="lalr", start='game', transformer=GameTransformer())


if __name__ == "__main__":
    assert game_parser.parse('ilya') == [['ilya']]
    assert game_parser.parse('ilya marat') == [['ilya', 'marat']]
    assert game_parser.parse('ilya vs marat') == [['ilya'], ['marat']]
    assert game_parser.parse('ilya vs marat liza') == [['ilya'], ['marat', 'liza']]
    assert game_parser.parse('ilya vs marat liza 5:') == [['ilya'], ['marat', 'liza'], [[5]]]
    assert game_parser.parse('ilya vs marat liza 5:4') == [['ilya'], ['marat', 'liza'], [[5, 4]]]
    assert game_parser.parse('ilya vs marat liza 5:4 3:') == [['ilya'], ['marat', 'liza'], [[5, 4], [3]]]





