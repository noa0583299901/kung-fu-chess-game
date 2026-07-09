"""
Unit tests for Position (iteration 1).
Tests: equality, inequality, readable representation, hashing.
"""
import pytest
from kungfu_chess.model.position import Position


class TestPosition:

    def test_two_positions_same_row_col_are_equal(self):
        assert Position(3, 4) == Position(3, 4)

    def test_two_positions_different_row_are_not_equal(self):
        assert Position(3, 4) != Position(5, 4)

    def test_two_positions_different_col_are_not_equal(self):
        assert Position(3, 4) != Position(3, 7)

    def test_position_not_equal_to_non_position(self):
        assert Position(0, 0) != (0, 0)
        assert Position(0, 0) != "Position(0,0)"

    def test_readable_representation(self):
        p = Position(2, 5)
        assert "2" in repr(p)
        assert "5" in repr(p)

    def test_hashable_for_use_in_sets_and_dicts(self):
        s = {Position(0, 0), Position(0, 0), Position(1, 1)}
        assert len(s) == 2
