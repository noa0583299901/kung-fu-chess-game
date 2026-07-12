"""
Tests to cover remaining gaps for 100% coverage.
Covers: app.py, script_runner edge cases, script_parser edge cases,
rule_engine source outside board, piece __repr__, motion default duration.
"""
import pytest
import io
import sys
from unittest.mock import patch

from kungfu_chess.model.position import Position
from kungfu_chess.model.piece import Piece, WHITE, BLACK, ROOK, KING, PAWN
from kungfu_chess.model.board import Board
from kungfu_chess.realtime.motion import calculate_duration
from kungfu_chess.rules.rule_engine import validate_move
from kungfu_chess.texttests.script_runner import run_script
from kungfu_chess.texttests.script_parser import parse_script


# --- app.py ---

class TestApp:

    def test_main_reads_stdin_and_runs(self):
        """app.main() reads from stdin and produces output."""
        input_lines = ["Board:", "wK .", "Commands:", "print board"]

        def fake_input():
            if input_lines:
                return input_lines.pop(0)
            raise EOFError()

        with patch("builtins.input", side_effect=fake_input):
            old = sys.stdout
            sys.stdout = buf = io.StringIO()
            from kungfu_chess.app import main
            main()
            sys.stdout = old
            output = buf.getvalue()
        assert "wK ." in output


# --- script_parser.py ---

class TestScriptParserEdgeCases:

    def test_missing_headers_returns_none(self):
        """No Board: or Commands: header."""
        result = parse_script(["click 50 50", "print board"])
        assert result == (None, None)

    def test_only_board_header_returns_board_and_empty_commands(self):
        """Board: with rows but no Commands: — returns board lines + empty commands."""
        board_lines, commands = parse_script(["Board:", "wK ."])
        assert board_lines == ["wK ."]
        assert commands == []

    def test_format_without_commands_header(self):
        """Board without Commands: — commands start at first click/wait/print."""
        board_lines, commands = parse_script([
            "Board", ". wR .", ". . .", "click 150 50", "print board"
        ])
        assert board_lines == [". wR .", ". . ."]
        assert commands == ["click 150 50", "print board"]


# --- script_runner.py ---

class TestScriptRunnerEdgeCases:

    def test_no_headers_does_nothing(self, capsys):
        """If parse_script returns None, run_script exits silently."""
        run_script(["just some random text"])
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_invalid_board_returns_early(self, capsys):
        """Empty board lines — parse_board returns None."""
        run_script(["Board:", "Commands:", "print board"])
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_board_with_error_prints_error(self, capsys):
        """Invalid token prints error message."""
        run_script(["Board:", "XX .", "Commands:", "print board"])
        captured = capsys.readouterr()
        assert "ERROR" in captured.out

    def test_empty_command_lines_skipped(self, capsys):
        """Empty lines in commands section are skipped."""
        run_script(["Board:", "wK .", "Commands:", "", "   ", "print board"])
        captured = capsys.readouterr()
        assert "wK ." in captured.out

    def test_unknown_command_is_ignored(self, capsys):
        """Unknown commands don't crash."""
        run_script(["Board:", "wK .", "Commands:", "fly 100 200", "print board"])
        captured = capsys.readouterr()
        assert "wK ." in captured.out


# --- rule_engine.py ---

class TestRuleEngineSourceOutside:

    def test_source_outside_board_returns_outside_board(self):
        board = Board(3, 3)
        result = validate_move(board, Position(10, 10), Position(0, 0))
        assert result.is_valid is False
        assert result.reason == "outside_board"

    def test_move_validation_bool_true_for_valid(self):
        board = Board(8, 8)
        rook = Piece(1, WHITE, ROOK, Position(0, 0))
        board.add_piece(rook)
        result = validate_move(board, Position(0, 0), Position(0, 3))
        assert bool(result) is True

    def test_move_validation_bool_false_for_invalid(self):
        board = Board(3, 3)
        result = validate_move(board, Position(10, 10), Position(0, 0))
        assert bool(result) is False


# --- piece.py __repr__ ---

class TestPieceRepr:

    def test_piece_repr_is_readable(self):
        piece = Piece(1, WHITE, KING, Position(3, 4))
        r = repr(piece)
        assert "white" in r
        assert "king" in r
        assert "3" in r
        assert "4" in r


# --- motion.py default duration ---

class TestMotionDefaultDuration:

    def test_unknown_piece_kind_uses_max_formula(self):
        """A piece with unknown kind still returns cells * MOVE_TIME_PER_CELL."""
        piece = Piece(1, WHITE, "unknown_kind", Position(0, 0))
        duration = calculate_duration(piece, Position(0, 0), Position(0, 3))
        assert duration == 3000  # max(0, 3) * 1000

    def test_knight_uses_sum_formula(self):
        """Knight: abs_dr + abs_dc."""
        piece = Piece(1, WHITE, "knight", Position(0, 0))
        duration = calculate_duration(piece, Position(0, 0), Position(2, 1))
        assert duration == 3000


# --- piece_rules.py edge cases ---

class TestPieceRulesEdgeCases:

    def test_pawn_at_top_edge_no_forward(self):
        """White pawn at row 0 — forward goes outside board."""
        board = Board(4, 4)
        pawn = Piece(1, WHITE, PAWN, Position(0, 0))
        board.add_piece(pawn)
        from kungfu_chess.rules.piece_rules import legal_destinations
        dests = legal_destinations(board, pawn)
        # row -1 is outside — should not be in destinations
        assert Position(-1, 0) not in dests

    def test_black_pawn_at_bottom_edge_no_forward(self):
        """Black pawn at last row — forward goes outside board."""
        board = Board(4, 4)
        pawn = Piece(1, BLACK, PAWN, Position(3, 0))
        board.add_piece(pawn)
        from kungfu_chess.rules.piece_rules import legal_destinations
        dests = legal_destinations(board, pawn)
        assert Position(4, 0) not in dests

    def test_unknown_piece_kind_returns_empty_set(self):
        """Unknown piece type returns no legal destinations."""
        board = Board(4, 4)
        piece = Piece(1, WHITE, "alien", Position(2, 2))
        board.add_piece(piece)
        from kungfu_chess.rules.piece_rules import legal_destinations
        dests = legal_destinations(board, piece)
        assert dests == set()
