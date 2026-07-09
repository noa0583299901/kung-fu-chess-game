"""
שכבה: RuleEngine
rule_engine — Validation Service.
בודק חוקיות מהלך מבוקש מול מצב הלוח הנוכחי.
Read-only — לא משנה את ה-Board.
תלוי ב-Board ו-PieceRules.
לא יודע על GameEngine, clicks, rendering, או timing.
"""
from kungfu_chess.model.position import Position
from kungfu_chess.model.board import Board
from kungfu_chess.model.piece import Piece, PAWN, QUEEN, ROOK, BISHOP, KNIGHT
from kungfu_chess.rules.piece_rules import is_valid_move_shape


# כלים "חולקים" — זזים לאורך שורה/עמודה/אלכסון ונחסמים בדרך
SLIDING_KINDS = (QUEEN, ROOK, BISHOP)


class MoveResult:
    """תוצאת בדיקת מהלך."""
    def __init__(self, legal: bool, reason: str = ""):
        self.legal = legal
        self.reason = reason

    def __bool__(self):
        return self.legal


def is_path_clear(board: Board, source: Position, dest: Position, kind: str) -> bool:
    """
    בודק שאין כלי בדרך עבור כלים חולקים ופאון כפול.
    """
    # פאון שזז 2 תאים — בודק שהתא האמצעי פנוי
    if kind == PAWN:
        if abs(dest.row - source.row) == 2:
            mid_row = (source.row + dest.row) // 2
            mid_pos = Position(mid_row, source.col)
            return board.get_piece_at(mid_pos) is None
        return True

    # סוס לא נחסם
    if kind == KNIGHT:
        return True

    # מלך זז תא אחד — לא נחסם
    if kind not in SLIDING_KINDS:
        return True

    # כלים חולקים — בודקים כל תא בדרך
    dr = dest.row - source.row
    dc = dest.col - source.col
    step_row = 0 if dr == 0 else (1 if dr > 0 else -1)
    step_col = 0 if dc == 0 else (1 if dc > 0 else -1)

    row = source.row + step_row
    col = source.col + step_col
    while (row, col) != (dest.row, dest.col):
        if board.get_piece_at(Position(row, col)) is not None:
            return False
        row += step_row
        col += step_col

    return True


def validate_move(board: Board, piece: Piece, dest: Position) -> MoveResult:
    """
    בודק אם מהלך מ-piece.cell ל-dest חוקי.
    לא משנה את ה-Board.
    """
    source = piece.cell

    # לא זז בכלל
    if source == dest:
        return MoveResult(False, "same_cell")

    # יעד מחוץ ללוח
    if not board.is_inside(dest):
        return MoveResult(False, "out_of_bounds")

    # בדיקת יעד — האם תפוס בכלי אותו צבע
    target_piece = board.get_piece_at(dest)
    if target_piece is not None and target_piece.color == piece.color:
        return MoveResult(False, "friendly_piece_at_dest")

    # target_occupied = יש שם כלי אויב (לבדיקת פאון)
    target_occupied = target_piece is not None

    # בדיקת צורת תנועה
    if not is_valid_move_shape(
        piece.kind, piece.color, source, dest,
        target_occupied, board.rows
    ):
        return MoveResult(False, "invalid_move_shape")

    # בדיקת חסימות
    if not is_path_clear(board, source, dest, piece.kind):
        return MoveResult(False, "path_blocked")

    return MoveResult(True)
