"""
שכבה: Text I/O
board_parser.py — ממיר ייצוג טקסטואלי של הלוח ל-Board עם Pieces.
תלוי ב-Model (Board, Piece, Position).
לא יודע על: חוקי שחמט, commands, rendering, timing.
"""
from kungfu_chess.model.position import Position
from kungfu_chess.model.piece import (
    Piece, WHITE, BLACK,
    KING, QUEEN, ROOK, BISHOP, KNIGHT, PAWN,
)
from kungfu_chess.model.board import Board

EMPTY_CELL = "."

# מיפוי אות לסוג כלי
KIND_MAP = {
    "K": KING,
    "Q": QUEEN,
    "R": ROOK,
    "B": BISHOP,
    "N": KNIGHT,
    "P": PAWN,
}

# מיפוי קידומת לצבע
COLOR_MAP = {
    "w": WHITE,
    "b": BLACK,
}

# אסימונים חוקיים
VALID_TOKENS = {
    ".",
    "wK", "wQ", "wR", "wB", "wN", "wP",
    "bK", "bQ", "bR", "bB", "bN", "bP",
}

# שגיאות
ERROR_ROW_WIDTH = "ERROR ROW_WIDTH_MISMATCH"
ERROR_UNKNOWN_TOKEN = "ERROR UNKNOWN_TOKEN"


def parse_board(board_lines: list) -> tuple:
    """
    מפרסר שורות טקסט ובונה Board.
    מחזיר (Board, None) אם תקין, או (None, error_message) אם לא.
    """
    if not board_lines:
        return None, None

    rows_data = [line.split() for line in board_lines]

    width = len(rows_data[0])
    for row in rows_data:
        if len(row) != width:
            return None, ERROR_ROW_WIDTH
        for token in row:
            if token not in VALID_TOKENS:
                return None, ERROR_UNKNOWN_TOKEN

    num_rows = len(rows_data)
    board = Board(num_rows, width)
    piece_id = 1

    for r, row in enumerate(rows_data):
        for c, token in enumerate(row):
            if token == EMPTY_CELL:
                continue
            color = COLOR_MAP[token[0]]
            kind = KIND_MAP[token[1]]
            pos = Position(r, c)
            piece = Piece(piece_id, color, kind, pos)
            board.add_piece(piece)
            piece_id += 1

    return board, None
