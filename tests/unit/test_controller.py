"""
Unit tests for Controller (iteration 2).
Uses a FAKE GameEngine to verify controller behavior in isolation.
Tests: selection, click routing, outside-board cancellation.
"""
import pytest
from kungfu_chess.model.position import Position
from kungfu_chess.model.piece import Piece, WHITE, BLACK, ROOK, KING
from kungfu_chess.model.board import Board
from kungfu_chess.input.controller import Controller


class FakeGameEngine:
    """Fake GameEngine for Controller unit tests — records calls."""

    def __init__(self, board: Board):
        self.board = board
        self.game_over = False
        self.motion_in_progress = False
        self.move_requests = []  # list of (source, destination)

    def request_move(self, source, destination):
        self.move_requests.append((source, destination))

    def get_snapshot(self):
        return None


class TestControllerSelection:

    def _make_board_with_rook(self):
        board = Board(3, 3)
        rook = Piece(1, WHITE, ROOK, Position(0, 0))
        board.add_piece(rook)
        return board, rook

    def test_first_click_on_piece_sets_selection(self):
        board, rook = self._make_board_with_rook()
        engine = FakeGameEngine(board)
        ctrl = Controller(engine)

        ctrl.handle_click(50, 50)  # (0,0) = rook
        assert ctrl.selected == Position(0, 0)

    def test_first_click_on_empty_cell_leaves_selection_empty(self):
        board, _ = self._make_board_with_rook()
        engine = FakeGameEngine(board)
        ctrl = Controller(engine)

        ctrl.handle_click(150, 150)  # (1,1) = empty
        assert ctrl.selected is None

    def test_second_in_board_click_sends_correct_source_and_destination(self):
        board, rook = self._make_board_with_rook()
        engine = FakeGameEngine(board)
        ctrl = Controller(engine)

        ctrl.handle_click(50, 50)   # select rook at (0,0)
        ctrl.handle_click(250, 50)  # second click at (0,2)

        assert len(engine.move_requests) == 1
        source, dest = engine.move_requests[0]
        assert source == Position(0, 0)
        assert dest == Position(0, 2)

    def test_second_in_board_click_clears_selection(self):
        board, _ = self._make_board_with_rook()
        engine = FakeGameEngine(board)
        ctrl = Controller(engine)

        ctrl.handle_click(50, 50)   # select
        ctrl.handle_click(250, 50)  # second click
        assert ctrl.selected is None

    def test_second_click_on_same_color_switches_selection(self):
        board = Board(3, 3)
        rook = Piece(1, WHITE, ROOK, Position(0, 0))
        knight = Piece(2, WHITE, KING, Position(0, 2))
        board.add_piece(rook)
        board.add_piece(knight)
        engine = FakeGameEngine(board)
        ctrl = Controller(engine)

        ctrl.handle_click(50, 50)   # select rook
        ctrl.handle_click(250, 50)  # click on friendly king — switches selection

        # No request_move sent — selection switched instead
        assert len(engine.move_requests) == 0
        assert ctrl.selected == Position(0, 2)


class TestControllerOutsideBoard:

    def test_outside_click_with_no_selection_is_ignored(self):
        board = Board(3, 3)
        engine = FakeGameEngine(board)
        ctrl = Controller(engine)

        ctrl.handle_click(999, 999)  # outside
        assert ctrl.selected is None
        assert len(engine.move_requests) == 0

    def test_outside_click_with_selection_cancels_and_does_not_call_engine(self):
        board = Board(3, 3)
        rook = Piece(1, WHITE, ROOK, Position(0, 0))
        board.add_piece(rook)
        engine = FakeGameEngine(board)
        ctrl = Controller(engine)

        ctrl.handle_click(50, 50)   # select rook
        ctrl.handle_click(999, 999)  # outside — cancels

        assert ctrl.selected is None
        assert len(engine.move_requests) == 0

    def test_negative_coords_with_selection_cancels(self):
        board = Board(3, 3)
        rook = Piece(1, WHITE, ROOK, Position(0, 0))
        board.add_piece(rook)
        engine = FakeGameEngine(board)
        ctrl = Controller(engine)

        ctrl.handle_click(50, 50)   # select
        ctrl.handle_click(-10, 50)  # negative — cancels

        assert ctrl.selected is None
        assert len(engine.move_requests) == 0

    def test_negative_coords_with_no_selection_ignored(self):
        board = Board(3, 3)
        engine = FakeGameEngine(board)
        ctrl = Controller(engine)

        ctrl.handle_click(-5, -5)
        assert ctrl.selected is None
