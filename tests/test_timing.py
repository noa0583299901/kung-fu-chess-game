import pytest
from game.timing import PendingMove, move_duration
from game.constants import (
    KING, QUEEN, ROOK, BISHOP, KNIGHT, PAWN,
    KING_MOVE_TIME, KNIGHT_MOVE_TIME, MOVE_TIME_PER_CELL,
    WHITE,
)


class TestPendingMove:
    def test_creation_with_defaults(self):
        move = PendingMove(
            source_row=0, source_col=0,
            target_row=1, target_col=1,
            duration=1000,
        )
        assert move.elapsed == 0

    def test_elapsed_can_be_updated(self):
        move = PendingMove(0, 0, 1, 1, duration=1000)
        move.elapsed += 500
        assert move.elapsed == 500

    def test_all_fields_stored(self):
        move = PendingMove(2, 3, 5, 6, duration=2000, elapsed=100)
        assert move.source_row == 2
        assert move.source_col == 3
        assert move.target_row == 5
        assert move.target_col == 6
        assert move.duration == 2000
        assert move.elapsed == 100


class TestMoveDuration:
    def test_king_duration(self):
        assert move_duration("wK", 4, 4, 4, 5) == KING_MOVE_TIME

    def test_knight_duration(self):
        assert move_duration("wN", 4, 4, 6, 5) == KNIGHT_MOVE_TIME

    def test_pawn_duration(self):
        assert move_duration("wP", 4, 4, 3, 4) == MOVE_TIME_PER_CELL

    def test_rook_duration_by_distance(self):
        # נע 5 תאים — מצפה ל-5 * MOVE_TIME_PER_CELL
        assert move_duration("wR", 4, 0, 4, 5) == 5 * MOVE_TIME_PER_CELL

    def test_bishop_duration_by_distance(self):
        # נע אלכסונית: abs_dr == abs_dc תמיד לבישוף חוקי.
        # הטסט מוודא שהתוצאה מדויקת לפי מספר הצעדים — לא ערך קבוע.
        assert move_duration("wB", 0, 0, 3, 3) == 3 * MOVE_TIME_PER_CELL
        assert move_duration("wB", 0, 0, 5, 5) == 5 * MOVE_TIME_PER_CELL
        # ווידוא שהתוצאה לא שווה לזמן מלך (קבוע, לא תלוי מרחק)
        assert move_duration("wB", 0, 0, 3, 3) != KING_MOVE_TIME

    def test_queen_duration_straight(self):
        # נע 4 תאים ישר
        assert move_duration("wQ", 0, 0, 0, 4) == 4 * MOVE_TIME_PER_CELL

    def test_queen_duration_diagonal(self):
        # נע 4 תאים אלכסוני
        assert move_duration("wQ", 0, 0, 4, 4) == 4 * MOVE_TIME_PER_CELL

    def test_unknown_piece_returns_default(self):
        # כלי לא מוכר — מחזיר MOVE_TIME_PER_CELL כברירת מחדל
        assert move_duration("wX", 0, 0, 0, 1) == MOVE_TIME_PER_CELL
