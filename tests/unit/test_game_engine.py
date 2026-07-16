"""
Unit tests for GameEngine (iterations 4 + 6).
Tests: game-over guard, motion_in_progress, validation delegation, capture, king capture.
"""
import pytest
from kungfu_chess.model.position import Position
from kungfu_chess.model.piece import Piece, WHITE, BLACK, ROOK, KING, PAWN, CAPTURED
from kungfu_chess.model.board import Board
from kungfu_chess.engine.game_engine import GameEngine


class TestGameEngineGuards:

    def test_rejects_move_when_game_over(self):
        board = Board(8, 8)
        rook = Piece(1, WHITE, ROOK, Position(0, 0))
        board.add_piece(rook)
        engine = GameEngine(board)
        engine.state.end_game(BLACK)

        result = engine.request_move(rook.cell, Position(0, 5))
        assert result.is_accepted is False
        assert result.reason == "game_over"

    def test_rejects_move_when_same_piece_already_moving(self):
        board = Board(8, 8)
        rook = Piece(1, WHITE, ROOK, Position(0, 0))
        board.add_piece(rook)
        engine = GameEngine(board)

        # Start first motion
        engine.request_move(rook.cell, Position(0, 3))
        # Try to move same piece again
        result = engine.request_move(Position(0, 0), Position(0, 5))
        assert result.is_accepted is False
        assert result.reason == "motion_in_progress"

    def test_game_over_checked_before_rule_engine(self):
        """Even a legal-looking move is rejected if game is over."""
        board = Board(8, 8)
        rook = Piece(1, WHITE, ROOK, Position(0, 0))
        board.add_piece(rook)
        engine = GameEngine(board)
        engine.state.end_game(BLACK)

        result = engine.request_move(rook.cell, Position(0, 5))
        assert result.reason == "game_over"


class TestGameEngineValidation:

    def test_legal_move_returns_ok(self):
        board = Board(8, 8)
        rook = Piece(1, WHITE, ROOK, Position(0, 0))
        board.add_piece(rook)
        engine = GameEngine(board)

        result = engine.request_move(rook.cell, Position(0, 5))
        assert result.is_accepted is True
        assert result.reason == "ok"

    def test_illegal_move_returns_rule_engine_reason(self):
        board = Board(8, 8)
        rook = Piece(1, WHITE, ROOK, Position(0, 0))
        board.add_piece(rook)
        engine = GameEngine(board)

        result = engine.request_move(rook.cell, Position(3, 3))
        assert result.is_accepted is False
        assert result.reason == "illegal_piece_move"

    def test_invalid_move_does_not_start_motion(self):
        board = Board(8, 8)
        rook = Piece(1, WHITE, ROOK, Position(0, 0))
        board.add_piece(rook)
        engine = GameEngine(board)

        engine.request_move(rook.cell, Position(3, 3))
        assert engine.motion_in_progress is False

    def test_invalid_move_does_not_mutate_board(self):
        board = Board(8, 8)
        rook = Piece(1, WHITE, ROOK, Position(0, 0))
        board.add_piece(rook)
        engine = GameEngine(board)

        engine.request_move(rook.cell, Position(3, 3))
        assert board.get_piece_at(Position(0, 0)) is rook


class TestGameEngineCapture:

    def test_non_king_capture_removes_piece_on_arrival(self):
        board = Board(8, 8)
        rook = Piece(1, WHITE, ROOK, Position(0, 0))
        enemy_pawn = Piece(2, BLACK, PAWN, Position(0, 3))
        board.add_piece(rook)
        board.add_piece(enemy_pawn)
        engine = GameEngine(board)

        engine.request_move(rook.cell, Position(0, 3))
        engine.wait(3000)

        assert board.get_piece_at(Position(0, 3)) is rook
        assert enemy_pawn.state == CAPTURED

    def test_king_capture_sets_game_over(self):
        board = Board(8, 8)
        rook = Piece(1, WHITE, ROOK, Position(0, 0))
        enemy_king = Piece(2, BLACK, KING, Position(0, 3))
        board.add_piece(rook)
        board.add_piece(enemy_king)
        engine = GameEngine(board)

        engine.request_move(rook.cell, Position(0, 3))
        engine.wait(3000)

        assert engine.game_over is True
        assert engine.state.winner == WHITE

    def test_after_game_over_further_moves_rejected(self):
        board = Board(8, 8)
        rook = Piece(1, WHITE, ROOK, Position(0, 0))
        enemy_king = Piece(2, BLACK, KING, Position(0, 3))
        rook2 = Piece(3, WHITE, ROOK, Position(7, 0))
        board.add_piece(rook)
        board.add_piece(enemy_king)
        board.add_piece(rook2)
        engine = GameEngine(board)

        engine.request_move(rook.cell, Position(0, 3))
        engine.wait(3000)
        result = engine.request_move(rook2.cell, Position(7, 5))
        assert result.is_accepted is False
        assert result.reason == "game_over"


class TestGameEngineWait:

    def test_wait_delegates_to_arbiter(self):
        board = Board(8, 8)
        rook = Piece(1, WHITE, ROOK, Position(0, 0))
        board.add_piece(rook)
        engine = GameEngine(board)

        engine.request_move(rook.cell, Position(0, 2))
        # Not enough time
        engine.wait(1000)
        # Piece still at source logically
        assert board.get_piece_at(Position(0, 0)) is rook
        assert board.get_piece_at(Position(0, 2)) is None

        # Enough time
        engine.wait(1000)
        assert board.get_piece_at(Position(0, 2)) is rook
        assert board.get_piece_at(Position(0, 0)) is None
