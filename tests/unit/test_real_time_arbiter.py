"""
Unit tests for RealTimeArbiter (iteration 5).
Tests: elapsed time, active motions, arrival, capture events, atomic resolution.
"""
import pytest
from kungfu_chess.model.position import Position
from kungfu_chess.model.piece import Piece, WHITE, BLACK, ROOK, KING, IDLE, MOVING, CAPTURED
from kungfu_chess.model.board import Board
from kungfu_chess.realtime.real_time_arbiter import RealTimeArbiter
from kungfu_chess.realtime.motion import MOVE_TIME_PER_CELL


class TestArbiterTiming:

    def test_after_999ms_piece_has_not_arrived(self):
        board = Board(8, 8)
        rook = Piece(1, WHITE, ROOK, Position(0, 0))
        board.add_piece(rook)
        arbiter = RealTimeArbiter()

        arbiter.start_motion(rook, Position(0, 1))
        event = arbiter.advance_time(999, board)

        assert event is None
        assert board.get_piece_at(Position(0, 0)) is rook
        assert board.get_piece_at(Position(0, 1)) is None

    def test_after_1000ms_for_one_square_piece_arrives(self):
        board = Board(8, 8)
        rook = Piece(1, WHITE, ROOK, Position(0, 0))
        board.add_piece(rook)
        arbiter = RealTimeArbiter()

        arbiter.start_motion(rook, Position(0, 1))
        event = arbiter.advance_time(1000, board)

        assert event is not None
        assert board.get_piece_at(Position(0, 1)) is rook
        assert board.get_piece_at(Position(0, 0)) is None

    def test_partial_wait_then_remaining_equals_full(self):
        board = Board(8, 8)
        rook = Piece(1, WHITE, ROOK, Position(0, 0))
        board.add_piece(rook)
        arbiter = RealTimeArbiter()

        arbiter.start_motion(rook, Position(0, 2))  # 2000ms
        arbiter.advance_time(800, board)
        arbiter.advance_time(700, board)
        event = arbiter.advance_time(500, board)  # total 2000

        assert event is not None
        assert board.get_piece_at(Position(0, 2)) is rook

    def test_multiple_waits_accumulate(self):
        board = Board(8, 8)
        rook = Piece(1, WHITE, ROOK, Position(0, 0))
        board.add_piece(rook)
        arbiter = RealTimeArbiter()

        arbiter.start_motion(rook, Position(0, 3))  # 3000ms
        arbiter.advance_time(1000, board)
        arbiter.advance_time(1000, board)
        event = arbiter.advance_time(1000, board)

        assert event is not None
        assert board.get_piece_at(Position(0, 3)) is rook


class TestArbiterMotionState:

    def test_has_active_motion_after_start(self):
        board = Board(8, 8)
        rook = Piece(1, WHITE, ROOK, Position(0, 0))
        board.add_piece(rook)
        arbiter = RealTimeArbiter()

        arbiter.start_motion(rook, Position(0, 3))
        assert arbiter.has_active_motion is True

    def test_no_active_motion_after_arrival(self):
        board = Board(8, 8)
        rook = Piece(1, WHITE, ROOK, Position(0, 0))
        board.add_piece(rook)
        arbiter = RealTimeArbiter()

        arbiter.start_motion(rook, Position(0, 1))
        arbiter.advance_time(1000, board)
        assert arbiter.has_active_motion is False

    def test_piece_state_moving_during_motion(self):
        board = Board(8, 8)
        rook = Piece(1, WHITE, ROOK, Position(0, 0))
        board.add_piece(rook)
        arbiter = RealTimeArbiter()

        arbiter.start_motion(rook, Position(0, 1))
        assert rook.state == MOVING

    def test_piece_state_idle_after_arrival(self):
        board = Board(8, 8)
        rook = Piece(1, WHITE, ROOK, Position(0, 0))
        board.add_piece(rook)
        arbiter = RealTimeArbiter()

        arbiter.start_motion(rook, Position(0, 1))
        arbiter.advance_time(1000, board)
        assert rook.state == IDLE


class TestArbiterCapture:

    def test_capture_on_arrival(self):
        board = Board(8, 8)
        rook = Piece(1, WHITE, ROOK, Position(0, 0))
        enemy = Piece(2, BLACK, KING, Position(0, 3))
        board.add_piece(rook)
        board.add_piece(enemy)
        arbiter = RealTimeArbiter()

        arbiter.start_motion(rook, Position(0, 3))
        events = arbiter.advance_time(3000, board)

        assert events is not None
        assert len(events) == 1
        assert events[0].captured_piece is enemy
        assert enemy.state == CAPTURED

    def test_king_captured_flag(self):
        board = Board(8, 8)
        rook = Piece(1, WHITE, ROOK, Position(0, 0))
        enemy_king = Piece(2, BLACK, KING, Position(0, 3))
        board.add_piece(rook)
        board.add_piece(enemy_king)
        arbiter = RealTimeArbiter()

        arbiter.start_motion(rook, Position(0, 3))
        events = arbiter.advance_time(3000, board)

        assert events[0].king_captured is True

    def test_non_king_capture_flag_false(self):
        board = Board(8, 8)
        rook = Piece(1, WHITE, ROOK, Position(0, 0))
        enemy_pawn = Piece(2, BLACK, ROOK, Position(0, 3))
        board.add_piece(rook)
        board.add_piece(enemy_pawn)
        arbiter = RealTimeArbiter()

        arbiter.start_motion(rook, Position(0, 3))
        events = arbiter.advance_time(3000, board)

        assert events[0].king_captured is False

    def test_no_capture_on_empty_destination(self):
        board = Board(8, 8)
        rook = Piece(1, WHITE, ROOK, Position(0, 0))
        board.add_piece(rook)
        arbiter = RealTimeArbiter()

        arbiter.start_motion(rook, Position(0, 3))
        events = arbiter.advance_time(3000, board)

        assert events[0].captured_piece is None
        assert events[0].king_captured is False
