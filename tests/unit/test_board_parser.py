"""
Unit tests for BoardParser (iteration 0).
Tests: rectangular parsing, token validation, inconsistent row rejection.
"""
import pytest
from kungfu_chess.io.board_parser import parse_board, ERROR_ROW_WIDTH, ERROR_UNKNOWN_TOKEN
from kungfu_chess.model.position import Position
from kungfu_chess.model.piece import WHITE, BLACK, KING, ROOK, KNIGHT


class TestBoardParserValid:

    def test_accepts_rectangular_board(self):
        board, error = parse_board(["wK . .", ". . .", ". . bK"])
        assert board is not None
        assert error is None
        assert board.rows == 3
        assert board.cols == 3

    def test_infers_dimensions_from_text(self):
        board, _ = parse_board(["wR . . bR", ". . . ."])
        assert board.rows == 2
        assert board.cols == 4

    def test_places_pieces_at_correct_positions(self):
        board, _ = parse_board(["wK . bR"])
        king = board.get_piece_at(Position(0, 0))
        assert king is not None
        assert king.color == WHITE
        assert king.kind == KING

        rook = board.get_piece_at(Position(0, 2))
        assert rook is not None
        assert rook.color == BLACK
        assert rook.kind == ROOK

    def test_empty_cells_return_none(self):
        board, _ = parse_board(["wK . ."])
        assert board.get_piece_at(Position(0, 1)) is None
        assert board.get_piece_at(Position(0, 2)) is None

    def test_assigns_unique_piece_ids(self):
        board, _ = parse_board(["wK wR wN"])
        pieces = board.all_pieces()
        ids = [p.id for p in pieces]
        assert len(set(ids)) == 3  # all unique


class TestBoardParserInvalid:

    def test_rejects_inconsistent_row_length(self):
        board, error = parse_board(["wK .", "wK wR wN"])
        assert board is None
        assert error == ERROR_ROW_WIDTH

    def test_rejects_unknown_token(self):
        board, error = parse_board(["wK XX ."])
        assert board is None
        assert error == ERROR_UNKNOWN_TOKEN

    def test_empty_input_returns_none(self):
        board, error = parse_board([])
        assert board is None
        assert error is None
