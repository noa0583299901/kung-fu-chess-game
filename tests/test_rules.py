import pytest
from game.rules import (
    is_sliding_piece,
    is_legal_pawn_move,
    is_legal_move,
    is_path_clear,
    can_capture,
)
from game.constants import (
    KING, QUEEN, ROOK, BISHOP, KNIGHT, PAWN,
    WHITE, BLACK, EMPTY_CELL,
)


def make_empty_board(rows=8, cols=8):
    return [[EMPTY_CELL] * cols for _ in range(rows)]


class TestIsSlidingPiece:
    def test_queen_is_sliding(self):
        assert is_sliding_piece(QUEEN) is True

    def test_rook_is_sliding(self):
        assert is_sliding_piece(ROOK) is True

    def test_bishop_is_sliding(self):
        assert is_sliding_piece(BISHOP) is True

    def test_king_is_not_sliding(self):
        assert is_sliding_piece(KING) is False

    def test_knight_is_not_sliding(self):
        assert is_sliding_piece(KNIGHT) is False

    def test_pawn_is_not_sliding(self):
        assert is_sliding_piece(PAWN) is False


class TestIsLegalPawnMove:
    def test_white_pawn_moves_up_one(self):
        assert is_legal_pawn_move(WHITE, -1, 0, EMPTY_CELL) is True

    def test_white_pawn_cannot_move_down(self):
        assert is_legal_pawn_move(WHITE, 1, 0, EMPTY_CELL) is False

    def test_black_pawn_moves_down_one(self):
        assert is_legal_pawn_move(BLACK, 1, 0, EMPTY_CELL) is True

    def test_black_pawn_cannot_move_up(self):
        assert is_legal_pawn_move(BLACK, -1, 0, EMPTY_CELL) is False

    def test_pawn_blocked_by_piece_ahead(self):
        assert is_legal_pawn_move(WHITE, -1, 0, "bP") is False

    def test_white_pawn_captures_diagonally(self):
        assert is_legal_pawn_move(WHITE, -1, 1, "bP") is True

    def test_white_pawn_cannot_capture_empty(self):
        assert is_legal_pawn_move(WHITE, -1, 1, EMPTY_CELL) is False

    def test_white_pawn_cannot_capture_own_piece(self):
        assert is_legal_pawn_move(WHITE, -1, 1, "wR") is False

    def test_pawn_invalid_direction(self):
        assert is_legal_pawn_move(WHITE, -2, 0, EMPTY_CELL) is False

    def test_white_pawn_at_board_edge_is_legal_pawn_move_unaware_of_bounds(self):
        # is_legal_pawn_move בודקת רק כיוון ומצב היעד — היא לא יודעת על גבולות הלוח.
        # פאון לבן שנמצא בשורה 0, dr=-1 עדיין מחזיר True.
        # ההגנה מפני מהלך מחוץ ללוח מסופקת על ידי is_inside_board ב-handle_click,
        # לא על ידי is_legal_pawn_move עצמה.
        assert is_legal_pawn_move(WHITE, -1, 0, EMPTY_CELL) is True

    def test_black_pawn_at_board_edge_is_legal_pawn_move_unaware_of_bounds(self):
        # פאון שחור בשורה האחרונה, dr=+1 — אותו עיקרון.
        assert is_legal_pawn_move(BLACK, 1, 0, EMPTY_CELL) is True


class TestIsLegalMove:
    def test_king_moves_one_step(self):
        board = make_empty_board()
        board[4][4] = "wK"
        assert is_legal_move(board, "wK", 4, 4, 4, 5) is True

    def test_king_cannot_move_two_steps(self):
        board = make_empty_board()
        board[4][4] = "wK"
        assert is_legal_move(board, "wK", 4, 4, 4, 6) is False

    def test_rook_moves_along_row(self):
        board = make_empty_board()
        board[4][0] = "wR"
        assert is_legal_move(board, "wR", 4, 0, 4, 7) is True

    def test_rook_moves_along_col(self):
        board = make_empty_board()
        board[0][4] = "wR"
        assert is_legal_move(board, "wR", 0, 4, 7, 4) is True

    def test_rook_cannot_move_diagonally(self):
        board = make_empty_board()
        board[0][0] = "wR"
        assert is_legal_move(board, "wR", 0, 0, 3, 3) is False

    def test_rook_cannot_stay_in_place(self):
        board = make_empty_board()
        board[4][4] = "wR"
        assert is_legal_move(board, "wR", 4, 4, 4, 4) is False

    def test_bishop_moves_diagonally(self):
        board = make_empty_board()
        board[0][0] = "wB"
        assert is_legal_move(board, "wB", 0, 0, 3, 3) is True

    def test_bishop_cannot_move_straight(self):
        board = make_empty_board()
        board[0][0] = "wB"
        assert is_legal_move(board, "wB", 0, 0, 0, 3) is False

    def test_queen_moves_straight(self):
        board = make_empty_board()
        board[4][4] = "wQ"
        assert is_legal_move(board, "wQ", 4, 4, 4, 7) is True

    def test_queen_moves_diagonally(self):
        board = make_empty_board()
        board[4][4] = "wQ"
        assert is_legal_move(board, "wQ", 4, 4, 7, 7) is True

    def test_queen_cannot_stay_in_place(self):
        board = make_empty_board()
        board[4][4] = "wQ"
        assert is_legal_move(board, "wQ", 4, 4, 4, 4) is False

    def test_knight_moves_L_shape(self):
        board = make_empty_board()
        board[4][4] = "wN"
        assert is_legal_move(board, "wN", 4, 4, 6, 5) is True

    def test_knight_moves_L_shape_other(self):
        board = make_empty_board()
        board[4][4] = "wN"
        assert is_legal_move(board, "wN", 4, 4, 5, 6) is True

    def test_knight_cannot_move_straight(self):
        board = make_empty_board()
        board[4][4] = "wN"
        assert is_legal_move(board, "wN", 4, 4, 4, 6) is False

    def test_pawn_moves_forward(self):
        board = make_empty_board()
        board[4][4] = "wP"
        assert is_legal_move(board, "wP", 4, 4, 3, 4) is True

    def test_unknown_piece_type_returns_false(self):
        board = make_empty_board()
        board[4][4] = "wX"
        assert is_legal_move(board, "wX", 4, 4, 4, 5) is False


class TestIsPathClear:
    def test_non_sliding_piece_always_clear(self):
        board = make_empty_board()
        board[4][4] = "wN"
        assert is_path_clear(board, "wN", 4, 4, 6, 5) is True

    def test_rook_path_clear(self):
        board = make_empty_board()
        board[4][0] = "wR"
        assert is_path_clear(board, "wR", 4, 0, 4, 7) is True

    def test_rook_path_blocked(self):
        board = make_empty_board()
        board[4][0] = "wR"
        board[4][3] = "bP"
        assert is_path_clear(board, "wR", 4, 0, 4, 7) is False

    def test_bishop_path_clear(self):
        board = make_empty_board()
        board[0][0] = "wB"
        assert is_path_clear(board, "wB", 0, 0, 4, 4) is True

    def test_bishop_path_blocked(self):
        board = make_empty_board()
        board[0][0] = "wB"
        board[2][2] = "bP"
        assert is_path_clear(board, "wB", 0, 0, 4, 4) is False

    def test_queen_path_clear_straight(self):
        board = make_empty_board()
        board[0][0] = "wQ"
        assert is_path_clear(board, "wQ", 0, 0, 0, 7) is True

    def test_queen_path_blocked_straight(self):
        board = make_empty_board()
        board[0][0] = "wQ"
        board[0][4] = "bP"
        assert is_path_clear(board, "wQ", 0, 0, 0, 7) is False


class TestCanCapture:
    def test_can_move_to_empty(self):
        assert can_capture("wK", EMPTY_CELL) is True

    def test_can_capture_enemy(self):
        assert can_capture("wK", "bP") is True

    def test_cannot_capture_own_piece(self):
        assert can_capture("wK", "wP") is False
