from dataclasses import dataclass

from game.constants import (
    KING, KNIGHT, PAWN, ROOK, BISHOP, QUEEN,
    KING_MOVE_TIME, KNIGHT_MOVE_TIME, MOVE_TIME_PER_CELL,
)
from game.pieces import get_type


@dataclass
class PendingMove:
    source_row: int
    source_col: int
    target_row: int
    target_col: int
    duration: int
    elapsed: int = 0


def move_duration(piece, r1, c1, r2, c2):
    abs_dr = abs(r2 - r1)
    abs_dc = abs(c2 - c1)
    piece_type = get_type(piece)

    if piece_type == KING:
        return KING_MOVE_TIME
    if piece_type == KNIGHT:
        return KNIGHT_MOVE_TIME
    if piece_type == PAWN:
        return MOVE_TIME_PER_CELL
    if piece_type == ROOK:
        return max(abs_dr, abs_dc) * MOVE_TIME_PER_CELL
    if piece_type == BISHOP:
        return abs_dr * MOVE_TIME_PER_CELL
    if piece_type == QUEEN:
        return max(abs_dr, abs_dc) * MOVE_TIME_PER_CELL

    return MOVE_TIME_PER_CELL
