"""
שכבה: RealTimeArbiter
motion.py — מייצג תנועה פעילה של כלי.
מחזיק מקור, יעד, משך זמן, וזמן שעבר.
לא יודע על Board, חוקי שחמט, clicks, או rendering.
"""
from kungfu_chess.model.position import Position
from kungfu_chess.model.piece import (
    Piece, KING, KNIGHT, PAWN, ROOK, BISHOP, QUEEN,
)

# זמנים קבועים
KING_MOVE_TIME = 1000
KNIGHT_MOVE_TIME = 3000
MOVE_TIME_PER_CELL = 1000


class Motion:
    def __init__(self, piece: Piece, source: Position, destination: Position, duration: int):
        self.piece = piece
        self.source = source
        self.destination = destination
        self.duration = duration
        self.elapsed = 0

    @property
    def finished(self) -> bool:
        return self.elapsed >= self.duration

    def advance(self, milliseconds: int):
        """מקדם את הזמן שעבר."""
        self.elapsed += milliseconds


def calculate_duration(piece: Piece, source: Position, destination: Position) -> int:
    """מחשב את משך התנועה לפי סוג הכלי והמרחק."""
    abs_dr = abs(destination.row - source.row)
    abs_dc = abs(destination.col - source.col)

    if piece.kind == KING:
        return KING_MOVE_TIME
    if piece.kind == KNIGHT:
        return KNIGHT_MOVE_TIME
    if piece.kind == PAWN:
        return abs_dr * MOVE_TIME_PER_CELL
    if piece.kind == ROOK:
        return max(abs_dr, abs_dc) * MOVE_TIME_PER_CELL
    if piece.kind == BISHOP:
        return abs_dr * MOVE_TIME_PER_CELL
    if piece.kind == QUEEN:
        return max(abs_dr, abs_dc) * MOVE_TIME_PER_CELL

    return MOVE_TIME_PER_CELL
