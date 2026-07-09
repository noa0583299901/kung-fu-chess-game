"""
Unit tests for BoardPrinter (iteration 0).
Tests: round-trip, correct output format.
"""
import pytest
from kungfu_chess.io.board_parser import parse_board
from kungfu_chess.io.board_printer import board_to_string, print_board
from kungfu_chess.model.position import Position
from kungfu_chess.model.piece import Piece, WHITE, BLACK, KING, ROOK, KNIGHT
from kungfu_chess.model.board import Board


class TestBoardPrinter:

    def test_round_trip_simple_board(self):
        """Parse then print returns original text."""
        original = "wK . bR\n. . .\n. wN bK"
        board, _ = parse_board(original.split("\n"))
        result = board_to_string(board)
        assert result == original

    def test_round_trip_single_row(self):
        original = "wR . . bK"
        board, _ = parse_board([original])
        result = board_to_string(board)
        assert result == original

    def test_all_empty_board(self):
        board = Board(2, 3)
        result = board_to_string(board)
        assert result == ". . .\n. . ."

    def test_prints_to_stdout(self, capsys):
        board, _ = parse_board(["wK ."])
        print_board(board)
        captured = capsys.readouterr()
        assert captured.out.strip() == "wK ."

    def test_prints_correct_piece_tokens(self):
        board, _ = parse_board(["wK wQ wR wB wN wP", "bK bQ bR bB bN bP"])
        result = board_to_string(board)
        assert result == "wK wQ wR wB wN wP\nbK bQ bR bB bN bP"
