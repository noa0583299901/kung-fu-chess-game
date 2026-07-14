"""
שכבה: Text I/O
board_printer.py — מדפיס את הלוח בפורמט טקסט.
Read-only — לא משנה דבר ב-Board.
תלוי ב-Model (Board, Piece, Position).
לא יודע על: חוקי שחמט, commands, rendering, timing.
"""
from kungfu_chess.model.position import Position
from kungfu_chess.model.board import Board
from kungfu_chess.model.piece import (
    WHITE, BLACK,
    KING, QUEEN, ROOK, BISHOP, KNIGHT, PAWN,
)
from kungfu_chess.constants import EMPTY_CELL

# מיפוי הפוך — מסוג כלי לאות
KIND_TO_LETTER = {
    KING: "K",
    QUEEN: "Q",
    ROOK: "R",
    BISHOP: "B",
    KNIGHT: "N",
    PAWN: "P",
}

# מיפוי צבע לקידומת
COLOR_TO_PREFIX = {
    WHITE: "w",
    BLACK: "b",
}


def piece_to_token(piece) -> str:
    """ממיר Piece לייצוג טקסטואלי כמו 'wR' או 'bK'."""
    prefix = COLOR_TO_PREFIX[piece.color]
    letter = KIND_TO_LETTER[piece.kind]
    return prefix + letter


def board_to_string(board: Board) -> str:
    """ממיר Board למחרוזת טקסט מוכנה להדפסה."""
    lines = []
    for r in range(board.rows):
        row_tokens = []
        for c in range(board.cols):
            piece = board.get_piece_at(Position(r, c))
            if piece is None:
                row_tokens.append(EMPTY_CELL)
            else:
                row_tokens.append(piece_to_token(piece))
        lines.append(" ".join(row_tokens))
    return "\n".join(lines)


def print_board(board: Board):
    """מדפיס את הלוח לstdout."""
    print(board_to_string(board))
