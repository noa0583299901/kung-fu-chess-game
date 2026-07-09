"""
שכבה: Model
GameState — מחזיק את מצב המשחק הכולל.
כרגע: האם המשחק נגמר ומי ניצח.
"""


class GameState:
    def __init__(self):
        self.game_over = False
        self.winner = None

    def end_game(self, winner_color: str):
        self.game_over = True
        self.winner = winner_color
