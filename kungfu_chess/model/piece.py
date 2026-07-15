"""
שכבה: Model
Piece — מייצג כלי שחמט.
יש לו id ייחודי, צבע, סוג, מיקום (cell), ומצב מחזור חיים (state).
לא יודע על renderer, עכבר, פיקסלים, או תחביר טסטים.
"""
from kungfu_chess.model.position import Position

# צבעים
WHITE = "white"
BLACK = "black"

# סוגי כלים
KING = "king"
QUEEN = "queen"
ROOK = "rook"
BISHOP = "bishop"
KNIGHT = "knight"
PAWN = "pawn"

# מצבי מחזור חיים
IDLE = "idle"
MOVING = "moving"
CAPTURED = "captured"
DEFENDING = "defending"
RESTING = "resting"


class Piece:
    def __init__(self, piece_id: int, color: str, kind: str, cell: Position):
        self.id = piece_id
        self.color = color
        self.kind = kind
        self.cell = cell
        self.state = IDLE

    def __repr__(self):
        return f"Piece(id={self.id}, color={self.color}, kind={self.kind}, cell={self.cell}, state={self.state})"
