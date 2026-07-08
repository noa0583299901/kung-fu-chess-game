import pytest
from game.commands import handle_click, handle_wait, process_commands
from game.timing import PendingMove
from game.constants import EMPTY_CELL


def make_board(*rows):
    """בונה לוח מרשימת שורות נתונות."""
    return [list(row) for row in rows]


def simple_board():
    """לוח 4x4 עם פאון לבן ב-(2,2)."""
    return [
        [EMPTY_CELL] * 4,
        [EMPTY_CELL] * 4,
        [EMPTY_CELL, EMPTY_CELL, "wP", EMPTY_CELL],
        [EMPTY_CELL] * 4,
    ]


class TestHandleClick:
    def test_selects_piece_on_first_click(self):
        board = simple_board()
        selected, pending = handle_click(["click", "200", "200"], board, None, None)
        assert selected == (2, 2)
        assert pending is None

    def test_ignores_click_on_empty_cell_when_nothing_selected(self):
        board = simple_board()
        selected, pending = handle_click(["click", "0", "0"], board, None, None)
        assert selected is None
        assert pending is None

    def test_ignores_click_while_pending(self):
        board = simple_board()
        pending = PendingMove(2, 2, 1, 2, duration=1000)
        selected, new_pending = handle_click(["click", "200", "200"], board, None, pending)
        assert selected is None
        assert new_pending is pending  # לא השתנה כלום

    def test_ignores_negative_coordinates(self):
        board = simple_board()
        selected, pending = handle_click(["click", "-1", "0"], board, None, None)
        assert selected is None

    def test_ignores_click_outside_board(self):
        board = simple_board()
        # פיקסל (9999, 9999) — מחוץ ללוח
        selected, pending = handle_click(["click", "9999", "9999"], board, None, None)
        assert selected is None

    def test_switches_selection_to_same_color_piece(self):
        board = simple_board()
        board[0][0] = "wR"
        # בוחרים את הצריח תחילה
        selected, _ = handle_click(["click", "0", "0"], board, None, None)
        assert selected == (0, 0)
        # לוחצים על הפאון — אותו צבע, צריך לעבור אליו
        selected, pending = handle_click(["click", "200", "200"], board, selected, None)
        assert selected == (2, 2)
        assert pending is None

    def test_illegal_move_deselects(self):
        board = simple_board()
        # פאון לבן ב-(2,2), מנסה ללכת שמאלה — לא חוקי
        selected = (2, 2)
        selected, pending = handle_click(["click", "100", "200"], board, selected, None)
        assert selected is None
        assert pending is None

    def test_blocked_path_deselects(self):
        # צריח לבן ב-(2,2) מנסה לנוע לשורה 0, אבל יש כלי שחור ב-(1,2) שחוסם
        board = [
            [EMPTY_CELL] * 4,
            [EMPTY_CELL, EMPTY_CELL, "bP", EMPTY_CELL],
            [EMPTY_CELL, EMPTY_CELL, "wR", EMPTY_CELL],
            [EMPTY_CELL] * 4,
        ]
        selected = (2, 2)
        selected, pending = handle_click(["click", "200", "0"], board, selected, None)
        assert selected is None
        assert pending is None

    def test_clicking_own_piece_switches_selection(self):
        # לחיצה על כלי מאותו צבע מחליפה את הבחירה — לא מבצעת מהלך
        board = [
            [EMPTY_CELL] * 4,
            [EMPTY_CELL, EMPTY_CELL, EMPTY_CELL, EMPTY_CELL],
            [EMPTY_CELL, EMPTY_CELL, "wP", EMPTY_CELL],
            ["wR", EMPTY_CELL, EMPTY_CELL, EMPTY_CELL],
        ]
        selected = (2, 2)  # בחרנו פאון לבן
        # לוחצים על הצריח הלבן — אמור לעבור אליו, לא לנסות מהלך
        selected, pending = handle_click(["click", "0", "300"], board, selected, None)
        assert selected == (3, 0)
        assert pending is None

    def test_valid_move_creates_pending(self):
        board = simple_board()
        selected = (2, 2)
        # פאון לבן נע קדימה ל-(1,2)
        new_selected, pending = handle_click(["click", "200", "100"], board, selected, None)
        assert new_selected is None
        assert isinstance(pending, PendingMove)
        assert pending.source_row == 2
        assert pending.source_col == 2
        assert pending.target_row == 1
        assert pending.target_col == 2


class TestPawnEdgeCases:
    def test_white_pawn_at_row_zero_cannot_move_via_handle_click(self):
        # handle_click מגן: קואורדינטות y שליליות נדחות לפני הכל.
        # אין דרך חוקית להניע פאון מחוץ לגבולות הלוח דרך handle_click.
        board = [
            ["wP", EMPTY_CELL, EMPTY_CELL, EMPTY_CELL],
            [EMPTY_CELL] * 4,
            [EMPTY_CELL] * 4,
            [EMPTY_CELL] * 4,
        ]
        selected = (0, 0)
        selected, pending = handle_click(["click", "0", "-100"], board, selected, None)
        assert selected == (0, 0)  # הבחירה לא השתנה
        assert pending is None

    def test_click_outside_board_top_boundary_ignored(self):
        # לחיצה שממפה לשורה שלילית דרך pixel_to_cell נדחית על ידי is_inside_board
        board = [
            ["wP", EMPTY_CELL],
            [EMPTY_CELL, EMPTY_CELL],
        ]
        selected = (0, 0)
        selected, pending = handle_click(["click", "50", "-50"], board, selected, None)
        assert pending is None

    def test_pawn_blocked_by_enemy_piece_directly_ahead(self):
        # פאון לבן ב-(2,0), יש כלי שחור ב-(1,0) ישירות קדימה.
        # פאון לא יכול לאכול ישר — המהלך לא חוקי.
        # (אכילה אלכסונית בלבד מותרת לפאון)
        board = [
            [EMPTY_CELL] * 4,
            ["bN", EMPTY_CELL, EMPTY_CELL, EMPTY_CELL],
            ["wP", EMPTY_CELL, EMPTY_CELL, EMPTY_CELL],
            [EMPTY_CELL] * 4,
        ]
        selected = (2, 0)
        selected, pending = handle_click(["click", "0", "100"], board, selected, None)
        assert selected is None
        assert pending is None
    def test_no_pending_returns_none(self):
        board = simple_board()
        result, game_over = handle_wait(["wait", "500"], board, None)
        assert result is None
        assert game_over is False

    def test_elapsed_not_enough_updates_pending(self):
        board = simple_board()
        board[2][2] = "wP"
        pending = PendingMove(2, 2, 1, 2, duration=1000, elapsed=0)
        result, game_over = handle_wait(["wait", "500"], board, pending)
        assert isinstance(result, PendingMove)
        assert result.elapsed == 500
        assert game_over is False

    def test_elapsed_exact_completes_move(self):
        board = simple_board()
        board[2][2] = "wP"
        pending = PendingMove(2, 2, 1, 2, duration=1000, elapsed=0)
        result, game_over = handle_wait(["wait", "1000"], board, pending)
        assert result is None
        assert game_over is False
        assert board[1][2] == "wP"
        assert board[2][2] == EMPTY_CELL

    def test_elapsed_over_completes_move(self):
        board = simple_board()
        board[2][2] = "wP"
        pending = PendingMove(2, 2, 1, 2, duration=1000, elapsed=800)
        result, game_over = handle_wait(["wait", "300"], board, pending)
        assert result is None
        assert game_over is False
        assert board[1][2] == "wP"


class TestProcessCommands:
    def test_full_sequence_pawn_move(self, capsys):
        board = [
            [EMPTY_CELL] * 4,
            [EMPTY_CELL] * 4,
            [EMPTY_CELL, EMPTY_CELL, "wP", EMPTY_CELL],
            [EMPTY_CELL] * 4,
        ]
        commands = [
            "click 200 200",   # בוחר פאון ב-(2,2)
            "click 200 100",   # שולח ל-(1,2)
            "wait 1000",       # מסיים את התנועה
            "print board",
        ]
        process_commands(commands, board)
        captured = capsys.readouterr()
        lines = captured.out.strip().split("\n")
        # שורה 1 צריכה להכיל wP בעמודה 2
        assert lines[1].split()[2] == "wP"
        # שורה 2 צריכה להיות ריקה
        assert lines[2].split()[2] == EMPTY_CELL

    def test_click_ignored_while_pending(self, capsys):
        board = [
            [EMPTY_CELL] * 4,
            [EMPTY_CELL] * 4,
            [EMPTY_CELL, EMPTY_CELL, "wP", EMPTY_CELL],
            [EMPTY_CELL, EMPTY_CELL, EMPTY_CELL, "bP"],
        ]
        commands = [
            "click 200 200",   # בוחר פאון לבן
            "click 200 100",   # שולח ל-(1,2) — pending נוצר
            "click 300 300",   # לחיצה תוך כדי תנועה — אמורה להתעלם
            "wait 1000",
            "print board",
        ]
        process_commands(commands, board)
        captured = capsys.readouterr()
        lines = captured.out.strip().split("\n")
        assert lines[1].split()[2] == "wP"

    def test_unknown_command_ignored(self):
        board = [[EMPTY_CELL] * 4] * 4
        # לא צריך לקרוס
        process_commands(["fly 100 100"], board)

    def test_empty_lines_skipped(self):
        board = [[EMPTY_CELL] * 4] * 4
        process_commands(["", "   ", ""], board)

    def test_print_without_board_arg_ignored(self, capsys):
        board = [["wP", "."]]
        process_commands(["print"], board)
        captured = capsys.readouterr()
        assert captured.out == ""
