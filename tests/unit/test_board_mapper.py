"""
Unit tests for BoardMapper (iteration 2).
Tests: pixel to cell mapping, boundaries.
"""
import pytest
from kungfu_chess.input.board_mapper import pixel_to_position, CELL_SIZE
from kungfu_chess.model.position import Position


class TestBoardMapper:

    def test_x_0_to_99_maps_to_col_0(self):
        assert pixel_to_position(0, 0).col == 0
        assert pixel_to_position(99, 0).col == 0

    def test_x_100_to_199_maps_to_col_1(self):
        assert pixel_to_position(100, 0).col == 1
        assert pixel_to_position(199, 0).col == 1

    def test_y_0_to_99_maps_to_row_0(self):
        assert pixel_to_position(0, 0).row == 0
        assert pixel_to_position(0, 99).row == 0

    def test_y_100_to_199_maps_to_row_1(self):
        assert pixel_to_position(0, 100).row == 1
        assert pixel_to_position(0, 199).row == 1

    def test_click_50_50_maps_to_row0_col0(self):
        assert pixel_to_position(50, 50) == Position(0, 0)

    def test_click_150_50_maps_to_row0_col1(self):
        assert pixel_to_position(150, 50) == Position(0, 1)

    def test_click_50_150_maps_to_row1_col0(self):
        assert pixel_to_position(50, 150) == Position(1, 0)
