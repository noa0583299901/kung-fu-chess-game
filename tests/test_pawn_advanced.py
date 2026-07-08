import pytest
from game.rules import is_legal_pawn_move, is_legal_move, is_path_clear
from game.board import promote_pawn_if_needed, move_piece
from game.commands import process_commands
from game.constants import (
    EMPTY_CELL, WHITE, BLACK, QUEEN, PAWN,
    MOVE_TIME_PER_CELL,
)
from game.pieces import get_type
from game.timing import move_duration


# ---------------------------------------------------------------------------
# עזרים
# ---------------------------------------------------------------------------

def make_empty_board(rows=8, cols=8):
    return [[EMPTY_CELL] * cols for _ in range(rows)]


# ---------------------------------------------------------------------------
# 1. פאון זז 2 תאים מהשורה ההתחלתית
# ---------------------------------------------------------------------------

class TestPawnDoubleMove:

    def test_white_pawn_can_move_two_from_start_row(self):
        # לבן מתחיל בשורה 6 בלוח 8x8
        board = make_empty_board()
        board[6][3] = "wP"
        assert is_legal_move(board, "wP", 6, 3, 4, 3) is True

    def test_black_pawn_can_move_two_from_start_row(self):
        # שחור מתחיל בשורה 1 בלוח 8x8
        board = make_empty_board()
        board[1][3] = "bP"
        assert is_legal_move(board, "bP", 1, 3, 3, 3) is True

    def test_white_pawn_cannot_move_two_from_non_start_row(self):
        # לבן שכבר זז — לא יכול לזוז 2
        board = make_empty_board()
        board[4][3] = "wP"
        assert is_legal_move(board, "wP", 4, 3, 2, 3) is False

    def test_black_pawn_cannot_move_two_from_non_start_row(self):
        # שחור שכבר זז — לא יכול לזוז 2
        board = make_empty_board()
        board[4][3] = "bP"
        assert is_legal_move(board, "bP", 4, 3, 6, 3) is False

    def test_pawn_cannot_move_two_diagonally(self):
        # 2 תאים אלכסונית — אסור בכל מקרה
        board = make_empty_board()
        board[6][3] = "wP"
        assert is_legal_move(board, "wP", 6, 3, 4, 5) is False

    def test_pawn_cannot_move_two_to_occupied_cell(self):
        # תא היעד תפוס — לא חוקי
        board = make_empty_board()
        board[6][3] = "wP"
        board[4][3] = "bP"
        assert is_legal_move(board, "wP", 6, 3, 4, 3) is False

    def test_white_pawn_start_row_in_small_board(self):
        # לוח 4x4 — שורת התחלה של לבן היא שורה 2
        board = [[EMPTY_CELL] * 4 for _ in range(4)]
        board[2][1] = "wP"
        assert is_legal_move(board, "wP", 2, 1, 0, 1) is True

    def test_black_pawn_start_row_in_small_board(self):
        # לוח 4x4 — שורת התחלה של שחור היא שורה 1
        board = [[EMPTY_CELL] * 4 for _ in range(4)]
        board[1][1] = "bP"
        assert is_legal_move(board, "bP", 1, 1, 3, 1) is True


# ---------------------------------------------------------------------------
# 2. הדרך חייבת להיות פנויה לתנועה כפולה
# ---------------------------------------------------------------------------

class TestPawnDoubleMovePath:

    def test_white_pawn_double_move_blocked_by_piece_in_middle(self):
        # יש כלי בתא האמצעי — לא יכול לדלג
        board = make_empty_board()
        board[6][3] = "wP"
        board[5][3] = "bP"  # חוסם
        assert is_path_clear(board, "wP", 6, 3, 4, 3) is False

    def test_white_pawn_double_move_path_clear(self):
        board = make_empty_board()
        board[6][3] = "wP"
        assert is_path_clear(board, "wP", 6, 3, 4, 3) is True

    def test_black_pawn_double_move_blocked_by_piece_in_middle(self):
        board = make_empty_board()
        board[1][3] = "bP"
        board[2][3] = "wP"  # חוסם
        assert is_path_clear(board, "bP", 1, 3, 3, 3) is False

    def test_single_move_pawn_is_not_blocked_by_path(self):
        # תנועה של תא אחד — is_path_clear אמורה להיות True תמיד
        board = make_empty_board()
        board[6][3] = "wP"
        assert is_path_clear(board, "wP", 6, 3, 5, 3) is True


# ---------------------------------------------------------------------------
# 3. פאון מגיע לשורה האחרונה — הופך למלכה
# ---------------------------------------------------------------------------

class TestPawnPromotion:

    def test_white_pawn_promoted_to_queen_at_row_zero(self):
        board = make_empty_board()
        board[1][3] = "wP"
        # מזיזים לשורה 0 ומפעילים קידום
        move_piece(board, 1, 3, 0, 3)
        promote_pawn_if_needed(board, 0, 3)
        assert board[0][3] == "wQ"

    def test_black_pawn_promoted_to_queen_at_last_row(self):
        board = make_empty_board(rows=8)
        board[6][3] = "bP"
        move_piece(board, 6, 3, 7, 3)
        promote_pawn_if_needed(board, 7, 3)
        assert board[7][3] == "bQ"

    def test_white_pawn_not_promoted_before_last_row(self):
        board = make_empty_board()
        board[3][3] = "wP"
        move_piece(board, 3, 3, 2, 3)
        promote_pawn_if_needed(board, 2, 3)
        assert board[2][3] == "wP"  # לא הופך

    def test_non_pawn_not_promoted(self):
        # מלכה בשורה 0 — לא אמורה להתרחש הפיכה
        board = make_empty_board()
        board[0][3] = "wQ"
        promote_pawn_if_needed(board, 0, 3)
        assert board[0][3] == "wQ"

    def test_empty_cell_not_promoted(self):
        board = make_empty_board()
        promote_pawn_if_needed(board, 0, 3)
        assert board[0][3] == EMPTY_CELL


# ---------------------------------------------------------------------------
# 4. אינטגרציה — זרימה מלאה עם process_commands
# ---------------------------------------------------------------------------

class TestPawnIntegration:

    def test_white_pawn_double_move_via_commands(self, capsys):
        # לוח 8x8 — לבן בשורה 6, זז 2 תאים
        board = make_empty_board()
        board[6][0] = "wP"
        commands = [
            "click 50 650",   # בוחר wP ב-(6,0)
            "click 50 450",   # שולח ל-(4,0)
            "wait 2000",
            "print board",
        ]
        process_commands(commands, board)
        captured = capsys.readouterr()
        lines = captured.out.strip().split("\n")
        assert lines[4].split()[0] == "wP"
        assert lines[6].split()[0] == EMPTY_CELL

    def test_white_pawn_promotes_via_commands(self, capsys):
        # פאון לבן צעד אחד מהקידום
        board = [[EMPTY_CELL] * 4 for _ in range(4)]
        board[1][0] = "wP"
        commands = [
            "click 50 150",   # בוחר wP ב-(1,0)
            "click 50 50",    # שולח ל-(0,0)
            "wait 1000",
            "print board",
        ]
        process_commands(commands, board)
        captured = capsys.readouterr()
        lines = captured.out.strip().split("\n")
        assert lines[0].split()[0] == "wQ"  # הפך למלכה
        assert lines[1].split()[0] == EMPTY_CELL

    def test_double_move_blocked_via_commands(self, capsys):
        # כלי חוסם את הדרך — הפאון לא זז
        board = make_empty_board()
        board[6][0] = "wP"
        board[5][0] = "bP"   # חוסם
        commands = [
            "click 50 650",
            "click 50 450",
            "wait 2000",
            "print board",
        ]
        process_commands(commands, board)
        captured = capsys.readouterr()
        lines = captured.out.strip().split("\n")
        assert lines[6].split()[0] == "wP"   # לא זז


# ---------------------------------------------------------------------------
# 5. move_duration לפאון כפול
# ---------------------------------------------------------------------------

class TestPawnDoubleDuration:

    def test_double_move_takes_two_cells_time(self):
        # פאון שזז 2 תאים — משך הזמן כפול
        assert move_duration("wP", 6, 0, 4, 0) == 2 * MOVE_TIME_PER_CELL

    def test_single_move_takes_one_cell_time(self):
        assert move_duration("wP", 6, 0, 5, 0) == MOVE_TIME_PER_CELL
