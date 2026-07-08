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
        # צריח לבן עם pending לנחות על מלך שחור — המהלך מסתיים וצריך להחזיר game_over=True
        board = [
            ["bK", EMPTY_CELL],
            ["wR", EMPTY_CELL],
        ]
        pending = PendingMove(1, 0, 0, 0, duration=1000, elapsed=0)
        new_pending, game_over = handle_wait(["wait", "1000"], board, pending)
        assert new_pending is None
        assert game_over is True

    def test_normal_move_does_not_trigger_game_over(self):
        # תנועה רגילה לתא ריק — game_over צריך להיות False
        board = [
            [EMPTY_CELL, EMPTY_CELL],
            ["wR", EMPTY_CELL],
        ]
        pending = PendingMove(1, 0, 0, 0, duration=1000, elapsed=0)
        new_pending, game_over = handle_wait(["wait", "1000"], board, pending)
        assert new_pending is None
        assert game_over is False

    def test_capturing_enemy_piece_not_king_does_not_trigger_game_over(self):
        # תפיסת כלי שחור שאינו מלך — game_over צריך להיות False
        board = [
            ["bQ", EMPTY_CELL],
            ["wR", EMPTY_CELL],
        ]
        pending = PendingMove(1, 0, 0, 0, duration=1000, elapsed=0)
        new_pending, game_over = handle_wait(["wait", "1000"], board, pending)
        assert new_pending is None
        assert game_over is False

    def test_no_pending_returns_no_game_over(self):
        # אין pending — game_over False, pending נשאר None
        board = [[EMPTY_CELL, EMPTY_CELL]]
        new_pending, game_over = handle_wait(["wait", "500"], board, None)
        assert new_pending is None
        assert game_over is False

    def test_move_not_finished_yet_no_game_over(self):
        # elapsed עדיין לא הגיע לduration — לא מסיים, לא game_over
        board = [
            [EMPTY_CELL, EMPTY_CELL],
            ["wR", EMPTY_CELL],
        ]
        pending = PendingMove(1, 0, 0, 0, duration=1000, elapsed=0)
        new_pending, game_over = handle_wait(["wait", "500"], board, pending)
        assert new_pending is not None
        assert game_over is False

    def test_capturing_white_king_triggers_game_over(self):
        # תפיסת מלך לבן על ידי כלי שחור — game_over גם כן
        board = [
            ["wK", EMPTY_CELL],
            ["bR", EMPTY_CELL],
        ]
        pending = PendingMove(1, 0, 0, 0, duration=1000, elapsed=0)
        new_pending, game_over = handle_wait(["wait", "1000"], board, pending)
        assert new_pending is None
        assert game_over is True


# ---------------------------------------------------------------------------
# process_commands — עצירה אחרי game-over
# ---------------------------------------------------------------------------

class TestProcessCommandsGameOver:

    def test_commands_after_king_capture_are_ignored(self, capsys):
        # צריח לבן אוכל מלך שחור, ואחרי זה יש עוד פקודות — אמורות להתעלם
        board = [
            ["bK", EMPTY_CELL, EMPTY_CELL],
            ["wR", EMPTY_CELL, EMPTY_CELL],
        ]
        commands = [
            "click 50 150",    # בוחר wR ב-(1,0)
            "click 50 50",     # שולח ל-(0,0) — נחסם על bK
            "wait 1000",       # מסיים תנועה — bK נאכל, game over
            "click 150 150",   # אמור להתעלם
            "print board",
        ]
        process_commands(commands, board)
        captured = capsys.readouterr()
        # אחרי game over אין print — הפקודה התעלמה
        assert captured.out == ""

    def test_print_before_game_over_works(self, capsys):
        # print לפני game-over עובד נורמלי, print אחרי game-over מתעלם
        board = [
            ["bK", EMPTY_CELL],
            ["wR", EMPTY_CELL],
        ]
        commands = [
            "print board",    # לפני game over — אמור להדפיס
            "click 50 150",
            "click 50 50",
            "wait 1000",
            "print board",    # אחרי game over — אמור להתעלם
        ]
        process_commands(commands, board)
        captured = capsys.readouterr()
        # הלוח הוא 2 שורות — print אחד = 2 שורות פלט.
        # שני print היה מדפיס 4 שורות. מוודאים שהודפסו בדיוק 2.
        lines = captured.out.strip().split("\n")
        assert len(lines) == 2
        # התוכן של הprint הראשון — לפני המהלך
        assert lines[0] == "bK ."
        assert lines[1] == "wR ."

    def test_wait_after_game_over_ignored(self):
        # wait אחרי game-over לא אמור לזוז כלי
        board = [
            ["bK", EMPTY_CELL],
            ["wR", EMPTY_CELL],
            [EMPTY_CELL, EMPTY_CELL],
        ]
        commands = [
            "click 50 150",   # בוחר wR
            "click 50 50",    # שולח ל-(0,0)
            "wait 1000",      # game over
            "click 50 50",    # אמור להתעלם — wR כבר אכל
            "click 50 250",   # אמור להתעלם
            "wait 1000",      # אמור להתעלם
        ]
        process_commands(commands, board)
        # הלוח לא אמור להשתנות אחרי game over
        assert board[0][0] == "wR"  # wR נמצא במיקומו הסופי
        assert board[1][0] == EMPTY_CELL  # המקור ריק

    def test_game_without_king_capture_continues_normally(self, capsys):
        # משחק שבו לא נאכל מלך — ממשיך לעבד פקודות
        board = [
            [EMPTY_CELL, EMPTY_CELL],
            ["wR", EMPTY_CELL],
        ]
        commands = [
            "click 50 150",   # בוחר wR
            "click 150 150",  # שולח ל-(1,1)
            "wait 1000",      # מסיים — אין game over
            "print board",    # אמור להדפיס
        ]
        process_commands(commands, board)
        captured = capsys.readouterr()
        assert captured.out != ""  # הדפיס משהו — לא עצר

    def test_full_game_over_sequence_board_state(self):
        # בדיקת מצב הלוח הסופי אחרי תפיסת מלך
        board = [
            ["bK", EMPTY_CELL],
            ["wR", EMPTY_CELL],
        ]
        commands = [
            "click 50 150",   # בוחר wR ב-(1,0)
            "click 50 50",    # שולח ל-(0,0) — אוכל bK
            "wait 1000",      # מסיים
        ]
        process_commands(commands, board)
        assert board[0][0] == "wR"
        assert board[1][0] == EMPTY_CELL
