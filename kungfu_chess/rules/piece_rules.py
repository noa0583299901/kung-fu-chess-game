"""
שכבה: Movement Rules
piece_rules — גיאומטריית תנועה לכל סוג כלי.
מקבלת מיקום מקור ויעד ומחזירה אם הצורה חוקית.
לא יודעת על Board state, חסימות, captures, או זמן.
תלויה רק ב-Position וב-piece kind/color.
Pattern: Strategy per piece type.
"""
from kungfu_chess.model.position import Position
from kungfu_chess.model.piece import (
    KING, QUEEN, ROOK, BISHOP, KNIGHT, PAWN, WHITE,
)


def is_valid_king_move(source: Position, dest: Position) -> bool:
    dr = abs(dest.row - source.row)
    dc = abs(dest.col - source.col)
    return max(dr, dc) == 1


def is_valid_rook_move(source: Position, dest: Position) -> bool:
    dr = abs(dest.row - source.row)
    dc = abs(dest.col - source.col)
    return (source.row == dest.row or source.col == dest.col) and (dr + dc > 0)


def is_valid_bishop_move(source: Position, dest: Position) -> bool:
    dr = abs(dest.row - source.row)
    dc = abs(dest.col - source.col)
    return dr == dc and dr > 0


def is_valid_queen_move(source: Position, dest: Position) -> bool:
    return is_valid_rook_move(source, dest) or is_valid_bishop_move(source, dest)


def is_valid_knight_move(source: Position, dest: Position) -> bool:
    dr = abs(dest.row - source.row)
    dc = abs(dest.col - source.col)
    return (dr == 2 and dc == 1) or (dr == 1 and dc == 2)


def is_valid_pawn_move(source: Position, dest: Position, color: str,
                       target_occupied: bool, board_rows: int) -> bool:
    """
    פאון — מורכב יותר כי תלוי בכיוון, שורת התחלה, ומצב היעד.
    target_occupied: האם יש כלי אויב ביעד (לאכילה אלכסונית).
    """
    direction = -1 if color == WHITE else 1
    start_row = board_rows - 1 if color == WHITE else 0
    dr = dest.row - source.row
    dc = dest.col - source.col

    # תנועה ישרה
    if dc == 0:
        if dr == direction and not target_occupied:
            return True
        if dr == 2 * direction and source.row == start_row and not target_occupied:
            return True
        return False

    # אכילה אלכסונית
    if abs(dc) == 1 and dr == direction:
        return target_occupied

    return False


def is_valid_move_shape(kind: str, color: str, source: Position, dest: Position,
                        target_occupied: bool, board_rows: int) -> bool:
    """
    נקודת כניסה ראשית — בודקת צורת תנועה לפי סוג הכלי.
    """
    if kind == KING:
        return is_valid_king_move(source, dest)
    if kind == ROOK:
        return is_valid_rook_move(source, dest)
    if kind == BISHOP:
        return is_valid_bishop_move(source, dest)
    if kind == QUEEN:
        return is_valid_queen_move(source, dest)
    if kind == KNIGHT:
        return is_valid_knight_move(source, dest)
    if kind == PAWN:
        return is_valid_pawn_move(source, dest, color, target_occupied, board_rows)
    return False
