import pytest
from game.commands import handle_wait, process_commands
from game.timing import PendingMove
from game.constants import EMPTY_CELL, KING
from game.pieces import get_type


# ---------------------------------------------------------------------------
# עזרים
# ---------------------------------------------------------------------------

def make_board(*rows):
    return [list(row) for row in rows]


# ---------------------------------------------------------------------------
# handle_wait — זיהוי תפיסת מלך
# ---------------------------------------------------------------------------

class TestHandleWaitGameOver:

    def test_capturing_enemy_king_returns_game_over(self):
        board = [
            ["bK", EMPTY_CELL],
            ["wR", EMPTY_CELL],
        ]
        pending = PendingMove(1, 0, 0, 0, duration=1000, elapsed=0)
        new_pending, game_over = handle_wait(["wait", "1000"], board, pending)
        assert new_pending is None
        assert game_over is True

    def test_normal_move_does_not_trigger_game_over(self):
        board = [
            [EMPTY_CELL, EMPTY_CELL],
            ["wR", EMPTY_CELL],
        ]
        pending = PendingMove(1, 0, 0, 0, duration=1000, elapsed=0)
        new_pending, game_over = handle_wait(["wait", "1000"], board, pending)
        assert new_pending is None
        assert game_over is False

    def test_capturing_enemy_piece_not_king_does_not_trigger_game_over(self):
        board = [
            ["bQ", EMPTY_CELL],
            ["wR", EMPTY_CELL],
        ]
        pending = PendingMove(1, 0, 0, 0, duration=1000, elapsed=0)
        new_pending, game_over = handle_wait(["wait", "1000"], board, pending)
        assert new_pending is None
        assert game_over is False

    def test_no_pending_returns_no_game_over(self):
        board = [[EMPTY_CELL, EMPTY_CELL]]
        new_pending, game_over = handle_wait(["wait", "500"], board, None)
        assert new_pending is None
        assert game_over is False

    def test_move_not_finished_yet_no_game_over(self):
        board = [
            [EMPTY_CELL, EMPTY_CELL],
            ["wR", EMPTY_CELL],
        ]
        pending = PendingMove(1, 0, 0, 0, duration=1000, elapsed=0)
        new_pending, game_over = handle_wait(["wait", "500"], board, pending)
        assert new_pending is not None
        assert game_over is False

    def test_capturing_white_king_triggers_game_over(self):
        board = [
            ["wK", EMPTY_CELL],
            ["bR", EMPTY_CELL],
        ]
        pending = PendingMove(1, 0, 0, 0, duration=1000, elapsed=0)
        new_pending, game_over = handle_wait(["wait", "1000"], board, pending)
        assert new_pending is None
        assert game_over is True


# ---------------------------------------------------------------------------
# process_commands — התנהגות אחרי game-over
# ---------------------------------------------------------------------------

class TestProcessCommandsGameOver:

    def test_click_after_king_capture_is_ignored(self):
        # click אחרי game-over לא אמור לבחור או להזיז כלים
        board = [
            ["bK", EMPTY_CELL, EMPTY_CELL],
            ["wR", EMPTY_CELL, EMPTY_CELL],
        ]
        commands = [
            "click 50 150",    # בוחר wR ב-(1,0)
            "click 50 50",     # שולח ל-(0,0)
            "wait 1000",       # מסיים — game over
            "click 150 50",    # אמור להתעלם — לא בוחר כלום
            "click 250 50",    # אמור להתעלם
        ]
        process_commands(commands, board)
        # הלוח לא השתנה אחרי game over
        assert board[0][0] == "wR"
        assert board[0][1] == EMPTY_CELL
        assert board[0][2] == EMPTY_CELL

    def test_wait_after_game_over_does_not_move_piece(self):
        # wait אחרי game-over לא אמור לזוז כלי
        board = [
            ["bK", EMPTY_CELL],
            ["wR", EMPTY_CELL],
            [EMPTY_CELL, EMPTY_CELL],
        ]
        commands = [
            "click 50 150",
            "click 50 50",
            "wait 1000",      # game over
            "click 50 50",    # אמור להתעלם
            "click 50 250",   # אמור להתעלם
            "wait 1000",      # אמור להתעלם
        ]
        process_commands(commands, board)
        assert board[0][0] == "wR"
        assert board[1][0] == EMPTY_CELL
        assert board[2][0] == EMPTY_CELL  # לא זז לשורה 2

    def test_print_works_after_game_over(self, capsys):
        # print עובד גם אחרי game-over — מראה את מצב הלוח הסופי
        board = [
            ["bK", EMPTY_CELL, EMPTY_CELL],
            ["wR", EMPTY_CELL, EMPTY_CELL],
        ]
        commands = [
            "click 50 150",
            "click 50 50",
            "wait 1000",       # game over
            "print board",     # אמור לעבוד
        ]
        process_commands(commands, board)
        captured = capsys.readouterr()
        assert captured.out.strip() == "wR . .\n. . ."

    def test_print_before_game_over_also_works(self, capsys):
        # print לפני game-over עובד, וגם אחריו
        board = [
            ["bK", EMPTY_CELL],
            ["wR", EMPTY_CELL],
        ]
        commands = [
            "print board",    # לפני — מדפיס מצב ראשוני
            "click 50 150",
            "click 50 50",
            "wait 1000",
            "print board",    # אחרי — מדפיס מצב סופי
        ]
        process_commands(commands, board)
        captured = capsys.readouterr()
        lines = captured.out.strip().split("\n")
        # 2 הדפסות × 2 שורות = 4 שורות
        assert len(lines) == 4
        assert lines[0] == "bK ."  # לפני המהלך
        assert lines[1] == "wR ."
        assert lines[2] == "wR ."  # אחרי המהלך
        assert lines[3] == ". ."

    def test_game_without_king_capture_continues_normally(self, capsys):
        board = [
            [EMPTY_CELL, EMPTY_CELL],
            ["wR", EMPTY_CELL],
        ]
        commands = [
            "click 50 150",
            "click 150 150",
            "wait 1000",
            "print board",
        ]
        process_commands(commands, board)
        captured = capsys.readouterr()
        assert captured.out != ""

    def test_full_game_over_sequence_board_state(self):
        board = [
            ["bK", EMPTY_CELL],
            ["wR", EMPTY_CELL],
        ]
        commands = [
            "click 50 150",
            "click 50 50",
            "wait 1000",
        ]
        process_commands(commands, board)
        assert board[0][0] == "wR"
        assert board[1][0] == EMPTY_CELL

    def test_platform_test1_king_capture(self, capsys):
        # שחזור טסט 1 של הפלטפורמה
        board = [["wR", EMPTY_CELL, "bK"]]
        commands = [
            "click 50 50",
            "click 250 50",
            "wait 2000",
            "print board",
        ]
        process_commands(commands, board)
        captured = capsys.readouterr()
        assert captured.out.strip() == ". . wR"

    def test_platform_test2_no_moves_after_game_over(self, capsys):
        # שחזור טסט 2 של הפלטפורמה
        board = [
            ["wR", EMPTY_CELL, "bK"],
            ["bR", EMPTY_CELL, EMPTY_CELL],
        ]
        commands = [
            "click 50 50",
            "click 250 50",
            "wait 2000",
            "click 50 150",
            "click 150 150",
            "wait 1000",
            "print board",
        ]
        process_commands(commands, board)
        captured = capsys.readouterr()
        assert captured.out.strip() == ". . wR\nbR . ."
