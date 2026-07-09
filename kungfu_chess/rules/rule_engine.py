"""
שכבה: RuleEngine (Validation Service)
rule_engine.py — בודק חוקיות מהלך מבוקש.
Read-only — לא משנה את ה-Board.
תלוי ב-Board ו-PieceRules.
לא יודע על GameEngine, clicks, rendering, timing, או game-over.
"""
from kungfu_chess.model.position import Position
from kungfu_chess.model.board import Board
from kungfu_chess.model.piece import Piece
from kungfu_chess.rules.piece_rules import legal_destinations


class MoveValidation:
    """תוצאת בדיקת חוקיות מהלך."""
    def __init__(self, is_valid: bool, reason: str):
        self.is_valid = is_valid
        self.reason = reason

    def __bool__(self):
        return self.is_valid


def validate_move(board: Board, source: Position, destination: Position) -> MoveValidation:
    """
    בודק אם מהלך מ-source ל-destination חוקי.
    לא משנה את ה-Board.
    """
    # יעד מחוץ ללוח
    if not board.is_inside(destination):
        return MoveValidation(False, "outside_board")

    # מקור מחוץ ללוח
    if not board.is_inside(source):
        return MoveValidation(False, "outside_board")

    # מקור ריק
    piece = board.get_piece_at(source)
    if piece is None:
        return MoveValidation(False, "empty_source")

    # יעד תפוס בכלי ידידותי
    target = board.get_piece_at(destination)
    if target is not None and target.color == piece.color:
        return MoveValidation(False, "friendly_destination")

    # שואלים את piece_rules אם היעד חוקי
    valid_dests = legal_destinations(board, piece)
    if destination not in valid_dests:
        return MoveValidation(False, "illegal_piece_move")

    return MoveValidation(True, "ok")
