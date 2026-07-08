from game.constants import (
    EMPTY_CELL,
    VALID_TOKENS,
    ERROR_ROW_WIDTH,
    ERROR_UNKNOWN_TOKEN,
    CELL_SIZE,
)


def is_inside_board(row, col, rows, cols):
    return 0 <= row < rows and 0 <= col < cols


def pixel_to_cell(x, y):
    return y // CELL_SIZE, x // CELL_SIZE


def validate_board(board):
    """
    מאמת שכל שורות הלוח שוות ברוחב וכל אסימון חוקי.
    מחזיר (True, None) אם תקין, אחרת (False, הודעת שגיאה).
    """
    if not board:
        return False, None

    width = len(board[0])
    for row in board:
        if len(row) != width:
            return False, ERROR_ROW_WIDTH
        for token in row:
            if token not in VALID_TOKENS:
                return False, ERROR_UNKNOWN_TOKEN

    return True, None


def print_board(board):
    for row in board:
        print(" ".join(row))


def is_king(piece):
    from game.pieces import get_type
    from game.constants import KING
    return piece != EMPTY_CELL and get_type(piece) == KING


def move_piece(board, source_row, source_col, target_row, target_col):
    piece = board[source_row][source_col]
    board[source_row][source_col] = EMPTY_CELL
    board[target_row][target_col] = piece
