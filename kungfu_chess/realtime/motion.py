"""
שכבה: RealTimeArbiter
motion.py — מייצג תנועה פעילה של כלי.
מחזיק מקור, יעד, משך זמן, וזמן שעבר.
לא יודע על Board, חוקי שחמט, clicks, או rendering.

Timing constants:
  CELL_SIZE = 100 pixels
  PIECE_SPEED = 100 pixels per second
  => time per cell = CELL_SIZE / PIECE_SPEED = 1000ms

Moving N squares takes N × 1000ms.
Diagonal movement uses cell-step duration, not Euclidean pixel distance.
Knight L-shape: abs_dr + abs_dc cell steps.
"""
from kungfu_chess.model.position import Position
from kungfu_chess.model.piece import Piece, KNIGHT

# Fixed constants for tests (from spec)
CELL_SIZE = 100          # pixels
PIECE_SPEED = 100        # pixels per second
MOVE_TIME_PER_CELL = (CELL_SIZE * 1000) // PIECE_SPEED  # = 1000ms


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
    """
    מחשב את משך התנועה.
    N squares × MOVE_TIME_PER_CELL.
    Knight: abs_dr + abs_dc cell steps (L-shape).
    All others: max(abs_dr, abs_dc) cell steps.
    """
    abs_dr = abs(destination.row - source.row)
    abs_dc = abs(destination.col - source.col)

    if piece.kind == KNIGHT:
        cells = abs_dr + abs_dc
    else:
        cells = max(abs_dr, abs_dc)

    return cells * MOVE_TIME_PER_CELL
