"""
שכבה: Engine
observer.py — Observer pattern interface.
GameEngine הוא ה-Subject שמודיע ל-Observers כשאירועים קורים.
Observers לא צריכים לדעת על מבנה פנימי של GameEngine.
"""


class GameEvent:
    """אירוע משחק בסיסי."""
    pass


class PieceMovedEvent(GameEvent):
    """אירוע — כלי סיים לנוע."""
    def __init__(self, piece_kind, color, source, destination, timestamp):
        self.piece_kind = piece_kind
        self.color = color
        self.source = source
        self.destination = destination
        self.timestamp = timestamp


class PieceCapturedEvent(GameEvent):
    """אירוע — כלי נאכל."""
    def __init__(self, captured_kind, captured_color, capturer_color, value):
        self.captured_kind = captured_kind
        self.captured_color = captured_color
        self.capturer_color = capturer_color
        self.value = value


class GameOverEvent(GameEvent):
    """אירוע — המשחק נגמר."""
    def __init__(self, winner_color):
        self.winner_color = winner_color


class GameObserver:
    """Interface ל-Observer — כל observer מממש את המתודות שרלוונטיות לו."""

    def on_piece_moved(self, event: PieceMovedEvent):
        pass

    def on_piece_captured(self, event: PieceCapturedEvent):
        pass

    def on_game_over(self, event: GameOverEvent):
        pass
