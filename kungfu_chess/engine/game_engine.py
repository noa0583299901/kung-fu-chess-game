"""
שכבה: GameEngine (Application Service)
game_engine.py — תיאום בין Board, RuleEngine, ו-RealTimeArbiter.
אחריות: game-over guard, validation delegation, הפעלת תנועות, wait delegation,
קידום פאון, ו-snapshots.
לא מכיל: לוגיקת תנועה ספציפית לכלי, rendering, input parsing, DSL parsing, pixel mapping.
"""
from kungfu_chess.model.board import Board
from kungfu_chess.model.game_state import GameState
from kungfu_chess.model.position import Position
from kungfu_chess.model.piece import Piece, PAWN, QUEEN, IDLE
from kungfu_chess.rules.rule_engine import validate_move, MoveResult
from kungfu_chess.realtime.real_time_arbiter import RealTimeArbiter, ArrivalEvent


class MoveResponse:
    """תגובה לבקשת מהלך."""
    def __init__(self, accepted: bool, reason: str = ""):
        self.accepted = accepted
        self.reason = reason


class GameEngine:
    def __init__(self, board: Board):
        self.board = board
        self.state = GameState()
        self._arbiter = RealTimeArbiter()

    @property
    def game_over(self) -> bool:
        return self.state.game_over

    @property
    def motion_in_progress(self) -> bool:
        return self._arbiter.has_active_motion

    def request_move(self, piece: Piece, destination: Position) -> MoveResponse:
        """
        מנסה להפעיל מהלך. מאמת חוקיות ומתחיל תנועה אם חוקי.
        """
        # game-over guard
        if self.state.game_over:
            return MoveResponse(False, "game_over")

        # תנועה פעילה — דוחה (common route: רק תנועה אחת בו-זמנית)
        if self._arbiter.has_active_motion:
            return MoveResponse(False, "motion_in_progress")

        # אימות חוקיות דרך RuleEngine
        result = validate_move(self.board, piece, destination)
        if not result.legal:
            return MoveResponse(False, result.reason)

        # מפעיל תנועה
        self._arbiter.start_motion(piece, destination)
        return MoveResponse(True)

    def wait(self, milliseconds: int):
        """
        מקדם זמן. אם תנועה מסתיימת — מטפל ב-arrival: capture, promotion, game-over.
        """
        if self.state.game_over:
            return None

        event = self._arbiter.advance_time(milliseconds, self.board)

        if event is not None:
            self._handle_arrival(event)

        return event

    def _handle_arrival(self, event: ArrivalEvent):
        """מטפל באירוע arrival — קידום פאון, game-over."""
        # קידום פאון
        piece = event.piece
        if piece.kind == PAWN:
            self._promote_if_needed(piece)

        # game-over
        if event.king_captured:
            winner = piece.color
            self.state.end_game(winner)

    def _promote_if_needed(self, piece: Piece):
        """פאון שהגיע לשורה האחרונה הופך למלכה."""
        last_row = 0 if piece.color == "white" else self.board.rows - 1
        if piece.cell.row == last_row:
            piece.kind = QUEEN
