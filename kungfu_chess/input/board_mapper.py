"""
שכבה: Input
board_mapper.py — Coordinate Adapter.
ממיר פיקסלים (x, y) ל-Position (row, col).
לא יודע על חוקי שחמט, Board state, rendering, או timing.
Pattern: Coordinate Adapter.
"""
from kungfu_chess.model.position import Position

CELL_SIZE = 100


def pixel_to_position(x: int, y: int) -> Position:
    """ממיר קואורדינטות פיקסל ל-Position על הלוח."""
    row = y // CELL_SIZE
    col = x // CELL_SIZE
    return Position(row, col)
