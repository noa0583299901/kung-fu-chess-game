"""
Unit tests for Board (iteration 1).
Tests: dimensions, piece lookup, empty cell, duplicate occupancy, move, remove.
"""
import pytest
from kungfu_chess.model.position import Position
from kungfu_chess.model.piece import Piece, WHITE, BLACK, KING, ROOK, KNIGHT, CAPTURED, IDLE
from kungfu_chess.model.board import Board


class TestBoardDimensions:

    def test_board_stores_rows_and_cols(self):
        board = Board(8, 8)
        assert board.rows == 8
        assert board.cols == 8

    def test_board_non_square(self):
        board = Board(3, 5)
        assert board.rows == 3
        assert board.cols == 5


class TestBoardIsInside:

    def test_inside_bounds(self):
        board = Board(8, 8)
        assert board.is_inside(Position(0, 0)) is True
        assert board.is_inside(Position(7, 7)) is True

    def test_outside_bounds(self):
        board = Board(8, 8)
        assert board.is_inside(Position(8, 0)) is False
        assert board.is_inside(Position(0, 8)) is False
        assert board.is_inside(Position(-1, 0)) is False


class TestBoardPieceLookup:

    def test_occupied_cell_returns_piece(self):
        board = Board(8, 8)
        king = Piece(1, WHITE, KING, Position(0, 0))
        board.add_piece(king)
        assert board.get_piece_at(Position(0, 0)) is king

    def test_empty_cell_returns_none(self):
        board = Board(8, 8)
        assert board.get_piece_at(Position(3, 3)) is None


class TestBoardAddPiece:

    def test_duplicate_occupancy_raises(self):
        board = Board(8, 8)
        p1 = Piece(1, WHITE, KING, Position(0, 0))
        p2 = Piece(2, BLACK, ROOK, Position(0, 0))
        board.add_piece(p1)
        with pytest.raises(ValueError):
            board.add_piece(p2)


class TestBoardMovePiece:

    def test_move_updates_source_and_destination(self):
        board = Board(8, 8)
        rook = Piece(1, WHITE, ROOK, Position(0, 0))
        board.add_piece(rook)

        board.move_piece(Position(0, 0), Position(0, 5))

        assert board.get_piece_at(Position(0, 0)) is None
        assert board.get_piece_at(Position(0, 5)) is rook
        assert rook.cell == Position(0, 5)

    def test_move_captures_enemy_at_destination(self):
        board = Board(8, 8)
        rook = Piece(1, WHITE, ROOK, Position(0, 0))
        king = Piece(2, BLACK, KING, Position(0, 5))
        board.add_piece(rook)
        board.add_piece(king)

        captured = board.move_piece(Position(0, 0), Position(0, 5))

        assert captured is king
        assert king.state == CAPTURED
        assert board.get_piece_at(Position(0, 5)) is rook


class TestBoardRemovePiece:

    def test_remove_clears_cell_and_marks_captured(self):
        board = Board(8, 8)
        knight = Piece(1, WHITE, KNIGHT, Position(3, 3))
        board.add_piece(knight)

        removed = board.remove_piece(Position(3, 3))

        assert removed is knight
        assert knight.state == CAPTURED
        assert board.get_piece_at(Position(3, 3)) is None

    def test_remove_empty_cell_returns_none(self):
        board = Board(8, 8)
        assert board.remove_piece(Position(0, 0)) is None


class TestPieceState:

    def test_piece_state_starts_idle(self):
        piece = Piece(1, WHITE, KING, Position(0, 0))
        assert piece.state == IDLE

    def test_piece_state_can_change_to_captured(self):
        piece = Piece(1, WHITE, KING, Position(0, 0))
        piece.state = CAPTURED
        assert piece.state == CAPTURED

    def test_piece_has_no_timing_or_destination_data(self):
        piece = Piece(1, WHITE, KING, Position(0, 0))
        assert not hasattr(piece, "destination")
        assert not hasattr(piece, "elapsed")
        assert not hasattr(piece, "duration")
