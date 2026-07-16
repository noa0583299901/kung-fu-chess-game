"""
שכבה: Rules
game_conditions.py — תנאי ניצחון וקידום כ-strategies ניתנות להחלפה.
Pattern: Strategy — ניתן להחליף כללי ניצחון וקידום בלי לשנות GameEngine.

דוגמה לשימוש עתידי:
- ניצחון לפי נקודות (במקום אכילת מלך)
- קידום לסוס במקום מלכה
- בלי קידום בכלל
"""
from abc import ABC, abstractmethod
from kungfu_chess.model.piece import Piece, KING, PAWN, QUEEN, WHITE


# ===========================================================================
# WinCondition — מתי המשחק נגמר
# ===========================================================================

class WinCondition(ABC):
    """Interface — מגדיר מתי המשחק נגמר ומי ניצח."""

    @abstractmethod
    def check(self, captured_piece: Piece, capturer_piece: Piece) -> str | None:
        """
        בודק אם המשחק נגמר אחרי capture.
        מחזיר את צבע המנצח, או None אם המשחק ממשיך.
        """
        pass


class KingCaptureWin(WinCondition):
    """ברירת מחדל — אכילת מלך מסיימת את המשחק."""

    def check(self, captured_piece: Piece, capturer_piece: Piece) -> str | None:
        if captured_piece.kind == KING:
            return capturer_piece.color
        return None


# ===========================================================================
# PromotionRule — מתי ואיך כלי מקודם
# ===========================================================================

class PromotionRule(ABC):
    """Interface — מגדיר מתי כלי מקודם ולמה."""

    @abstractmethod
    def check(self, piece: Piece, board_rows: int) -> str | None:
        """
        בודק אם כלי צריך לקבל קידום.
        מחזיר kind חדש (e.g. "queen") או None אם אין קידום.
        """
        pass


class PawnToQueenPromotion(PromotionRule):
    """ברירת מחדל — פאון שמגיע לשורה האחרונה הופך למלכה."""

    def check(self, piece: Piece, board_rows: int) -> str | None:
        if piece.kind != PAWN:
            return None
        last_row = 0 if piece.color == WHITE else board_rows - 1
        if piece.cell.row == last_row:
            return QUEEN
        return None


class NoPromotion(PromotionRule):
    """אין קידום — לשימוש במשחקים שלא רוצים promotion."""

    def check(self, piece: Piece, board_rows: int) -> str | None:
        return None
