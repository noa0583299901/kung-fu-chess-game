import pytest
from game.pieces import get_color, get_type, same_color
from game.constants import WHITE, BLACK, KING, PAWN, EMPTY_CELL


class TestGetColor:
    def test_white_piece(self):
        assert get_color("wK") == WHITE

    def test_black_piece(self):
        assert get_color("bP") == BLACK


class TestGetType:
    def test_king(self):
        assert get_type("wK") == KING

    def test_pawn(self):
        assert get_type("bP") == PAWN


class TestSameColor:
    def test_same_color_white(self):
        assert same_color("wK", "wP") is True

    def test_same_color_black(self):
        assert same_color("bK", "bP") is True

    def test_different_colors(self):
        assert same_color("wK", "bP") is False

    def test_first_is_empty(self):
        assert same_color(EMPTY_CELL, "wK") is False

    def test_second_is_empty(self):
        assert same_color("wK", EMPTY_CELL) is False

    def test_both_empty(self):
        assert same_color(EMPTY_CELL, EMPTY_CELL) is False
