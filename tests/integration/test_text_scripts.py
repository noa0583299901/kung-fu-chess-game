"""
Integration tests — run .kfc scripts through the public command path.
Each test calls ScriptRunner and compares print board output to expected.
"""
import pytest
import io
import sys
from kungfu_chess.texttests.script_runner import run_script


def run_and_capture(lines):
    """Runs a script and captures stdout."""
    old = sys.stdout
    sys.stdout = buf = io.StringIO()
    run_script(lines)
    sys.stdout = old
    return buf.getvalue()


class TestIteration5RealTimeMovement:
    """
    Iteration 5 text test:
    Rook moves 2 cells down. After 1000ms (partial) board is unchanged.
    After another 1000ms (total 2000) board updates.
    """

    def test_partial_then_full_arrival(self):
        lines = [
            "Board:",
            ". wR .",
            ". . .",
            ". . bK",
            "Commands:",
            "click 150 50",
            "click 150 250",
            "wait 1000",
            "print board",
            "wait 1000",
            "print board",
        ]
        output = run_and_capture(lines)
        prints = output.strip().split("\n\n") if "\n\n" in output else None

        # Split by "print board" outputs — each is 3 lines for a 3x3 board
        lines_out = output.strip().split("\n")
        # First print (after 1000ms — not arrived yet)
        assert lines_out[0] == ". wR ."
        assert lines_out[1] == ". . ."
        assert lines_out[2] == ". . bK"
        # Second print (after 2000ms — arrived)
        assert lines_out[3] == ". . ."
        assert lines_out[4] == ". . ."
        assert lines_out[5] == ". wR bK"


class TestIteration6CaptureAndGameOver:
    """
    Iteration 6 text test:
    Rook captures king. Then knight tries to move — game over, board unchanged.
    """

    def test_king_capture_and_game_over_blocks_further_moves(self):
        lines = [
            "Board:",
            "wR . bK",
            ". . wN",
            ". . .",
            "Commands:",
            "click 50 50",
            "click 250 50",
            "wait 2000",
            "print board",
            "click 250 150",
            "click 50 250",
            "wait 2000",
            "print board",
        ]
        output = run_and_capture(lines)
        lines_out = output.strip().split("\n")
        # First print — rook captured king
        assert lines_out[0] == ". . wR"
        assert lines_out[1] == ". . wN"
        assert lines_out[2] == ". . ."
        # Second print — game over, nothing changed
        assert lines_out[3] == ". . wR"
        assert lines_out[4] == ". . wN"
        assert lines_out[5] == ". . ."


class TestIteration8InvalidMoves:
    """
    Iteration 8 text test:
    Rook blocked by friendly pawn — board remains unchanged.
    """

    def test_blocked_rook_leaves_board_unchanged(self):
        lines = [
            "Board:",
            "wR wP .",
            ". . .",
            ". . bK",
            "Commands:",
            "click 50 50",
            "click 250 50",
            "wait 3000",
            "print board",
        ]
        output = run_and_capture(lines)
        lines_out = output.strip().split("\n")
        assert lines_out[0] == "wR wP ."
        assert lines_out[1] == ". . ."
        assert lines_out[2] == ". . bK"


class TestIteration0TrivialBoardPrint:
    """Iteration 0: trivial board print."""

    def test_simple_board_print(self):
        lines = [
            "Board:",
            ". . .",
            ". wK .",
            ". . .",
            "Commands:",
            "print board",
        ]
        output = run_and_capture(lines)
        lines_out = output.strip().split("\n")
        assert lines_out[0] == ". . ."
        assert lines_out[1] == ". wK ."
        assert lines_out[2] == ". . ."
