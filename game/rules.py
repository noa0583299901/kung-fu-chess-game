from game.constants import (
    EMPTY_CELL,
    KING, QUEEN, ROOK, BISHOP, KNIGHT, PAWN,
    WHITE,
)
from game.pieces import get_type, get_color


# כלים החוסמים דרכם (זזים לאורך שורה/עמודה/אלכסון)
def is_sliding_piece(piece_type):
    return piece_type in (QUEEN, ROOK, BISHOP)


def is_legal_pawn_move(color, dr, dc, target):
    direction = -1 if color == WHITE else 1
    if dc == 0:
        return dr == direction and target == EMPTY_CELL
    if abs(dc) == 1 and dr == direction:
        return target != EMPTY_CELL and get_color(target) != color
    return False


def is_legal_move(board, piece, r1, c1, r2, c2):
    dr = r2 - r1
    dc = c2 - c1
    abs_dr = abs(dr)
    abs_dc = abs(dc)
    piece_type = get_type(piece)
    color = get_color(piece)
    target = board[r2][c2]

    if piece_type == KING:
        return max(abs_dr, abs_dc) == 1

    if piece_type == ROOK:
        return (r1 == r2 or c1 == c2) and (abs_dr + abs_dc > 0)

    if piece_type == BISHOP:
        return abs_dr == abs_dc and abs_dr > 0

    if piece_type == QUEEN:
        return (
            (r1 == r2 or c1 == c2) or (abs_dr == abs_dc)
        ) and (abs_dr + abs_dc > 0)

    if piece_type == KNIGHT:
        return (abs_dr == 2 and abs_dc == 1) or (abs_dr == 1 and abs_dc == 2)

    if piece_type == PAWN:
        return is_legal_pawn_move(color, dr, dc, target)

    return False


def is_path_clear(board, piece, r1, c1, r2, c2):
    piece_type = get_type(piece)

    if not is_sliding_piece(piece_type):
        return True

    dr = r2 - r1
    dc = c2 - c1
    step_row = 0 if dr == 0 else dr // abs(dr)
    step_col = 0 if dc == 0 else dc // abs(dc)

    row = r1 + step_row
    col = c1 + step_col
    while (row, col) != (r2, c2):
        if board[row][col] != EMPTY_CELL:
            return False
        row += step_row
        col += step_col

    return True


def can_capture(piece, target):
    if target == EMPTY_CELL:
        return True
    return get_color(piece) != get_color(target)
