"""
Unit tests for RuleEngine (iterations 4 + 8).
Tests: stable validation reasons, read-only behavior.
"""
import pytest
from kungfu_chess.model.position import Position
from kungfu_chess.model.piece import Piece, WHITE, BLACK, ROOK, KING, PAWN
from kungfu_chess.model.board import Board
from kungfu_chess.rules.rule_engine import validate_move


class TestRuleEngineValid:

    def test_legal_rook_move_returns_ok(self):
        board = Board(8, 8)
        rook = Piece(1, WHITE, ROOK, Position(0, 0))
        board.add_piece(rook)
        result = validate_move(board, Position(0, 0), Position(0, 5))
        assert result.is_valid is True
        assert result.reason == "ok"

    def test_legal_move_does_not_mutate_board(self):
        board = Board(8, 8)
        rook = Piece(1, WHITE, ROOK, Position(0, 0))
        board.add_piece(rook)
        validate_move(board, Position(0, 0), Position(0, 5))
        # Board unchanged
        assert board.get_piece_at(Position(0, 0)) is rook
        assert board.get_piece_at(Position(0, 5)) is None


class TestRuleEngineInvalid:

    def test_outside_board_returns_outside_board(self):
        board = Board(3, 3)
        rook = Piece(1, WHITE, ROOK, Position(0, 0))
        board.add_piece(rook)
        result = validate_move(board, Position(0, 0), Position(0, 10))
        assert result.is_valid is False
        assert result.reason == "outside_board"

    def test_empty_source_returns_empty_source(self):
        board = Board(8, 8)
        result = validate_move(board, Position(3, 3), Position(3, 5))
        assert result.is_valid is False
        assert result.reason == "empty_source"

    def test_friendly_destination_returns_friendly_destination(self):
        board = Board(8, 8)
        rook = Piece(1, WHITE, ROOK, Position(0, 0))
        pawn = Piece(2, WHITE, PAWN, Position(0, 3))
        board.add_piece(rook)
        board.add_piece(pawn)
        result = validate_move(board, Position(0, 0), Position(0, 3))
        assert result.is_valid is False
        assert result.reason == "friendly_destination"

    def test_illegal_piece_move_returns_illegal_piece_move(self):
        board = Board(8, 8)
        rook = Piece(1, WHITE, ROOK, Position(0, 0))
        board.add_piece(rook)
        # Rook cannot move diagonally
        result = validate_move(board, Position(0, 0), Position(3, 3))
        assert result.is_valid is False
        assert result.reason == "illegal_piece_move"

    def test_blocked_path_returns_illegal_piece_move(self):
        board = Board(8, 8)
        rook = Piece(1, WHITE, ROOK, Position(0, 0))
        blocker = Piece(2, WHITE, PAWN, Position(0, 2))
        board.add_piece(rook)
        board.add_piece(blocker)
        # Rook tries to pass blocker
        result = validate_move(board, Position(0, 0), Position(0, 5))
        assert result.is_valid is False
        assert result.reason == "illegal_piece_move"

    def test_invalid_move_does_not_mutate_board(self):
        board = Board(8, 8)
        rook = Piece(1, WHITE, ROOK, Position(0, 0))
        board.add_piece(rook)
        validate_move(board, Position(0, 0), Position(3, 3))
        assert board.get_piece_at(Position(0, 0)) is rook

    def test_rule_engine_does_not_know_about_game_over(self):
        """RuleEngine has no game_over concept — that's GameEngine's job."""
        board = Board(8, 8)
        rook = Piece(1, WHITE, ROOK, Position(0, 0))
        board.add_piece(rook)
        # Even if we imagine game is over, RuleEngine still validates normally
        result = validate_move(board, Position(0, 0), Position(0, 5))
        assert result.is_valid is True
