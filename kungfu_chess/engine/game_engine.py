"""
שכבה: GameEngine (Application Service)
game_engine.py — תיאום בין Board, RuleEngine, ו-RealTimeArbiter.
הוא ה-public command boundary ש-Controller ו-TextTestRunner משתמשים בו.
אחריות: game-over guard, motion_in_progress guard, validation delegation,
הפעלת תנועות, wait delegation, king-capture notification, snapshots.
לא מכיל: לוגיקת תנועה ספציפית לכלי, pixel mapping, rendering, text parsing.
Pattern: Application Service.
"""
from kungfu_chess.model.board import Board
from kungfu_chess.model.game_state import GameState
from kungfu_chess.model.position import Position
from kungfu_chess.model.piece import Piece, KING, PAWN, QUEEN, WHITE, DEFENDING
from kungfu_chess.rules.rule_engine import validate_move
from kungfu_chess.realtime.real_time_arbiter import RealTimeArbiter, ArrivalEvent
from kungfu_chess.realtime.motion import MOVE_TIME_PER_CELL, Motion


class MoveResult:
    """תוצאת בקשת מהלך."""
    def __init__(self, is_accepted: bool, reason: str):
        self.is_accepted = is_accepted
        self.reason = reason


class GameSnapshot:
    """Read-only view model / DTO עבור renderer ו-printer."""
    def __init__(self, board: Board, game_over: bool, winner):
        self.board = board
        self.game_over = game_over
        self.winner = winner


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

    def request_move(self, source: Position, destination: Position) -> MoveResult:
        """
        מנסה להפעיל מהלך.
        API: request_move(source, destination) -> MoveResult
        סדר בדיקות: game-over → motion_in_progress → RuleEngine → start motion.
        """
        # game-over guard
        if self.state.game_over:
            return MoveResult(False, "game_over")

        # common route: רק תנועה אחת בו-זמנית
        if self._arbiter.has_active_motion:
            return MoveResult(False, "motion_in_progress")

        # validation דרך RuleEngine
        validation = validate_move(self.board, source, destination)
        if not validation.is_valid:
            return MoveResult(False, validation.reason)

        # מוצא את הכלי ב-source
        piece = self.board.get_piece_at(source)

        # מפעיל תנועה
        self._arbiter.start_motion(piece, destination)
        return MoveResult(True, "ok")

    def wait(self, milliseconds: int):
        """
        מקדם זמן. אם תנועה מסתיימת — מטפל ב-arrival ו-king-capture.
        """
        if self.state.game_over:
            return None

        event = self._arbiter.advance_time(milliseconds, self.board)

        if event is not None:
            self._handle_arrival(event)

        return event

    def _handle_arrival(self, event: ArrivalEvent):
        """מטפל באירוע arrival — promotion, king-capture notification."""
        piece = event.piece

        # promotion — פאון שמגיע לשורה האחרונה הופך למלכה
        if piece.kind == PAWN:
            last_row = 0 if piece.color == WHITE else self.board.rows - 1
            if piece.cell.row == last_row:
                piece.kind = QUEEN

        # game-over
        if event.king_captured:
            winner = piece.color
            self.state.end_game(winner)

    def jump(self, position: Position):
        """
        מסמן כלי כ-'defending' למשך תנועה של תא אחד (1000ms).
        אחרי שה-duration עוברת, הכלי חוזר ל-IDLE.
        Extra route: airborne/collision behavior.
        """
        piece = self.board.get_piece_at(position)
        if piece is not None:
            piece.state = DEFENDING
            motion = Motion(piece, position, position, MOVE_TIME_PER_CELL)
            self._arbiter.set_jump_motion(motion)

    def get_snapshot(self) -> GameSnapshot:
        """מחזיר snapshot read-only למצב הנוכחי."""
        return GameSnapshot(self.board, self.state.game_over, self.state.winner)
