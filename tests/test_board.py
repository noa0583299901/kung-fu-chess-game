import pytest
from game.board import (
    is_inside_board,
    pixel_to_cell,
    validate_board,
    print_board,
    move_piece,
)
from game.constants import (
    EMPTY_CELL,
    ERROR_ROW_WIDTH,
    ERROR_UNKNOWN_TOKEN,
    CELL_SIZE,
)


class TestIsInsideBoard:
    def test_top_left_corner(self):
        assert is_inside_board(0, 0, 8, 8) is True

    def test_bottom_right_corner(self):
        assert is_inside_board(7, 7, 8, 8) is True

    def test_row_out_of_bounds(self):
        assert is_inside_board(8, 0, 8, 8) is False

    def test_col_out_of_bounds(self):
        assert is_inside_board(0, 8, 8, 8) is False

    def test_negative_row(self):
        assert is_inside_board(-1, 0, 8, 8) is False

    def test_negative_col(self):
        assert is_inside_board(0, -1, 8, 8) is False


class TestPixelToCell:
    def test_top_left_pixel(self):
        assert pixel_to_cell(0, 0) == (0, 0)

    def test_middle_of_cell(self):
        # פיקסל (150, 250) — x=150 -> col=1, y=250 -> row=2
        assert pixel_to_cell(150, 250) == (2, 1)

    def test_exact_cell_boundary(self):
        # פיקסל (100, 100) — תחילת תא (1,1)
        assert pixel_to_cell(100, 100) == (1, 1)

    def test_cell_size_minus_one(self):
        # פיקסל (99, 99) — עדיין בתא (0,0)
        assert pixel_to_cell(99, 99) == (0, 0)


class TestValidateBoard:
    def make_valid_board(self):
        return [
            ["wR", "wN", "wB", "wQ", "wK", "wB", "wN", "wR"],
            ["wP", "wP", "wP", "wP", "wP", "wP", "wP", "wP"],
            ["."] * 8,
            ["."] * 8,
            ["."] * 8,
            ["."] * 8,
            ["bP", "bP", "bP", "bP", "bP", "bP", "bP", "bP"],
            ["bR", "bN", "bB", "bQ", "bK", "bB", "bN", "bR"],
        ]

    def test_valid_board(self):
        board = self.make_valid_board()
        valid, error = validate_board(board)
        assert valid is True
        assert error is None

    def test_empty_board_returns_false(self):
        valid, error = validate_board([])
        assert valid is False
        assert error is None

    def test_row_width_mismatch(self):
        board = self.make_valid_board()
        board[0].append("wR")  # שורה ראשונה ארוכה מדי
        valid, error = validate_board(board)
        assert valid is False
        assert error == ERROR_ROW_WIDTH

    def test_unknown_token(self):
        board = self.make_valid_board()
        board[0][0] = "XX"  # אסימון לא חוקי
        valid, error = validate_board(board)
        assert valid is False
        assert error == ERROR_UNKNOWN_TOKEN


class TestPrintBoard:
    def test_prints_rows(self, capsys):
        board = [["wP", "."], [".", "bP"]]
        print_board(board)
        captured = capsys.readouterr()
        assert captured.out == "wP .\n. bP\n"


class TestMovePiece:
    def test_piece_moves_to_target(self):
        board = [["wP", "."], [".", "."]]
        move_piece(board, 0, 0, 1, 1)
        assert board[1][1] == "wP"

    def test_source_becomes_empty(self):
        board = [["wP", "."], [".", "."]]
        move_piece(board, 0, 0, 1, 1)
        assert board[0][0] == EMPTY_CELL

    def test_capture_overwrites_target(self):
        board = [["wP", "bP"], [".", "."]]
        move_piece(board, 0, 0, 0, 1)
        assert board[0][1] == "wP"
        assert board[0][0] == EMPTY_CELL
