import pytest
from game.parser import parse_input
from game.constants import BOARD_HEADER, COMMANDS_HEADER


class TestParseInput:
    def make_input(self, board_rows, commands):
        lines = [BOARD_HEADER] + board_rows + [COMMANDS_HEADER] + commands
        return lines

    def test_valid_input_returns_board_and_commands(self):
        lines = self.make_input(
            ["wP . .", ". . .", ". . ."],
            ["click 50 50", "print board"],
        )
        board, command_lines = parse_input(lines)
        assert board == [["wP", ".", "."], [".", ".", "."], [".", ".", "."]]
        assert command_lines == ["click 50 50", "print board"]

    def test_missing_board_header_returns_none(self):
        lines = [COMMANDS_HEADER, "click 0 0"]
        board, command_lines = parse_input(lines)
        assert board is None
        assert command_lines is None

    def test_missing_commands_header_returns_none(self):
        lines = [BOARD_HEADER, "wP ."]
        board, command_lines = parse_input(lines)
        assert board is None
        assert command_lines is None

    def test_empty_lines_are_filtered(self):
        lines = [BOARD_HEADER, "", "wP .", "", COMMANDS_HEADER, "", "print board", ""]
        board, command_lines = parse_input(lines)
        assert board == [["wP", "."]]
        assert command_lines == ["print board"]

    def test_empty_commands_section(self):
        lines = self.make_input(["wP ."], [])
        board, command_lines = parse_input(lines)
        assert board == [["wP", "."]]
        assert command_lines == []

    def test_board_with_multiple_rows(self):
        lines = self.make_input(["wR wN", "wP wP"], ["print board"])
        board, command_lines = parse_input(lines)
        assert len(board) == 2
        assert board[0] == ["wR", "wN"]
        assert board[1] == ["wP", "wP"]
