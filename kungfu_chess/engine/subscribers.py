"""
שכבה: Engine
subscribers.py — מאזינים שנרשמים ל-EventBus.

כל subscriber הוא class שמגיב לאירועים שהוא מקבל מה-Bus.
ה-GameEngine לא מכיר אותם — רק ה-Bus מעביר להם הודעות.
"""
from kungfu_chess.constants import PIECE_VALUES


class ScoreSubscriber:
    """מעדכן ניקוד כשכלי נאכל."""

    def __init__(self):
        self.white_score = 0
        self.black_score = 0

    def on_piece_captured(self, data: dict):
        """נקרא כשכלי נאכל. data כולל: captured_kind, capturer_color, value."""
        value = data.get("value", 0)
        capturer_color = data.get("capturer_color")
        if capturer_color == "white":
            self.white_score += value
        else:
            self.black_score += value


class MoveLogSubscriber:
    """שומר היסטוריית מהלכים."""

    def __init__(self):
        self.moves = []  # list of dicts

    def on_piece_moved(self, data: dict):
        """נקרא כשכלי סיים לנוע. data כולל: piece_kind, color, destination, timestamp."""
        self.moves.append(data)

    def get_white_moves(self):
        return [m for m in self.moves if m.get("color") == "white"]

    def get_black_moves(self):
        return [m for m in self.moves if m.get("color") == "black"]


class SoundSubscriber:
    """מנגן צלילים בתגובה לאירועים (placeholder — להוספת sound בעתיד)."""

    def on_piece_moved(self, data: dict):
        pass  # עתיד: play move sound

    def on_piece_captured(self, data: dict):
        pass  # עתיד: play capture sound

    def on_game_over(self, data: dict):
        pass  # עתיד: play victory sound


class AnimationSubscriber:
    """מפעיל אנימציות game start/end."""

    def __init__(self):
        self.game_started = False
        self.game_ended = False
        self.winner = None

    def on_game_start(self, data: dict):
        self.game_started = True

    def on_game_over(self, data: dict):
        self.game_ended = True
        self.winner = data.get("winner")
