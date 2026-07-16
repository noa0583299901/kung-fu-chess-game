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
from kungfu_chess.model.piece import Piece, KING, PAWN, QUEEN, WHITE, DEFENDING, RESTING, IDLE
from kungfu_chess.rules.rule_engine import validate_move
from kungfu_chess.realtime.real_time_arbiter import RealTimeArbiter, ArrivalEvent
from kungfu_chess.realtime.motion import MOVE_TIME_PER_CELL, Motion
from kungfu_chess.constants import REASON_OK, REASON_GAME_OVER, REASON_MOTION_IN_PROGRESS, PIECE_VALUES, COOLDOWN_DURATION_MS, JUMP_COOLDOWN_MS
from kungfu_chess.engine.observer import (
    GameObserver, PieceMovedEvent, PieceCapturedEvent, GameOverEvent
)
import time


class MoveResult:
    """תוצאת בקשת מהלך."""
    def __init__(self, is_accepted: bool, reason: str):
        self.is_accepted = is_accepted
        self.reason = reason


class MoveLogEntry:
    """רשומה ב-moves log."""
    def __init__(self, piece_kind: str, color: str, source: Position, destination: Position, timestamp: float):
        self.piece_kind = piece_kind
        self.color = color
        self.source = source
        self.destination = destination
        self.timestamp = timestamp  # seconds since game start

    def time_str(self):
        """מחזיר זמן בפורמט MM:SS.mmm"""
        minutes = int(self.timestamp) // 60
        seconds = self.timestamp % 60
        millis = int((seconds % 1) * 1000)
        return f"{minutes:02d}:{int(seconds):02d}.{millis:03d}"

    def __repr__(self):
        col_letters = "abcdefgh"
        dst_col = col_letters[self.destination.col] if self.destination.col < 8 else "?"
        dst_row = str(8 - self.destination.row)
        kind_letter = self.piece_kind[0].upper() if self.piece_kind != "pawn" else ""
        return f"{kind_letter}{dst_col}{dst_row}"


class GameSnapshot:
    """Read-only view model / DTO עבור renderer ו-printer."""
    def __init__(self, board: Board, game_over: bool, winner,
                 white_score: int, black_score: int, moves_log: list):
        self.board = board
        self.game_over = game_over
        self.winner = winner
        self.white_score = white_score
        self.black_score = black_score
        self.moves_log = moves_log


class GameEngine:
    def __init__(self, board: Board):
        self.board = board
        self.state = GameState()
        self._arbiter = RealTimeArbiter()
        self._white_score = 0
        self._black_score = 0
        self._moves_log = []
        self._start_time = None  # יאותחל בלחיצה הראשונה
        self._observers = []
        self._resting_pieces = {}  # piece_id -> expire_time
        self._promotion_message = None  # (message, expire_time)

    def add_observer(self, observer: GameObserver):
        """רושם observer שיקבל הודעות על אירועי משחק."""
        self._observers.append(observer)

    def _notify_piece_moved(self, event: PieceMovedEvent):
        for obs in self._observers:
            obs.on_piece_moved(event)

    def _notify_piece_captured(self, event: PieceCapturedEvent):
        for obs in self._observers:
            obs.on_piece_captured(event)

    def _notify_game_over(self, event: GameOverEvent):
        for obs in self._observers:
            obs.on_game_over(event)

    @property
    def game_over(self) -> bool:
        return self.state.game_over

    @property
    def motion_in_progress(self) -> bool:
        return self._arbiter.has_active_motion

    def request_move(self, source: Position, destination: Position) -> MoveResult:
        """
        מנסה להפעיל מהלך.
        Kung Fu Chess: מספר תנועות במקביל מותר.
        מגביל: כלי ספציפי לא יכול לנוע אם הוא כבר בתנועה.
        """
        if self.state.game_over:
            return MoveResult(False, REASON_GAME_OVER)

        validation = validate_move(self.board, source, destination)
        if not validation.is_valid:
            return MoveResult(False, validation.reason)

        piece = self.board.get_piece_at(source)

        # כלי ב-cooldown לא יכול לנוע
        if piece.state == RESTING:
            return MoveResult(False, "cooldown")

        # כלי שכבר בתנועה לא יכול לנוע שוב
        if self._arbiter.is_piece_moving(piece.id):
            return MoveResult(False, REASON_MOTION_IN_PROGRESS)

        self._arbiter.start_motion(piece, destination)

        # מאתחל שעון בלחיצה הראשונה
        if self._start_time is None:
            self._start_time = time.time()

        return MoveResult(True, REASON_OK)

    def wait(self, milliseconds: int):
        """
        מקדם זמן. אם תנועה מסתיימת — מטפל ב-arrival ו-king-capture.
        גם בודק cooldown expiry.
        """
        if self.state.game_over:
            return None

        # בודק cooldown expiry
        now = time.time()
        expired = [pid for pid, expire in self._resting_pieces.items() if now >= expire]
        for pid in expired:
            del self._resting_pieces[pid]
            # מחזיר את הכלי ל-IDLE
            for p in self.board.all_pieces():
                if p.id == pid and p.state == RESTING:
                    p.state = IDLE
                    break

        # בודק כלים שנחתו מ-jump ונכנסו ל-resting (הArbiter שינה אותם)
        for p in self.board.all_pieces():
            if p.state == RESTING and p.id not in self._resting_pieces:
                self._resting_pieces[p.id] = now + JUMP_COOLDOWN_MS / 1000.0

        events = self._arbiter.advance_time(milliseconds, self.board)

        if events is not None:
            for event in events:
                self._handle_arrival(event)

        return events

    def _handle_arrival(self, event: ArrivalEvent):
        """מטפל באירוע arrival — log, score, promotion, king-capture, notify observers."""
        piece = event.piece
        elapsed = time.time() - self._start_time if self._start_time else 0.0

        # moves log
        self._moves_log.append(MoveLogEntry(
            piece.kind, piece.color, event.destination, event.destination, elapsed
        ))

        # notify: piece moved
        self._notify_piece_moved(PieceMovedEvent(
            piece.kind, piece.color, event.destination, event.destination, elapsed
        ))

        # score + notify: capture
        if event.captured_piece is not None:
            value = PIECE_VALUES.get(event.captured_piece.kind, 0)
            if piece.color == WHITE:
                self._white_score += value
            else:
                self._black_score += value

            self._notify_piece_captured(PieceCapturedEvent(
                event.captured_piece.kind, event.captured_piece.color,
                piece.color, value
            ))

        # promotion
        if piece.kind == PAWN:
            last_row = 0 if piece.color == WHITE else self.board.rows - 1
            if piece.cell.row == last_row:
                piece.kind = QUEEN
                color_name = "White" if piece.color == WHITE else "Black"
                self._promotion_message = (f"{color_name} Pawn promoted to Queen!", time.time() + 3.0)

        # game-over + notify
        if event.king_captured:
            winner = piece.color
            self.state.end_game(winner)
            self._notify_game_over(GameOverEvent(winner))

        # cooldown — כלי עובר ל-RESTING
        piece.state = RESTING
        self._resting_pieces[piece.id] = time.time() + COOLDOWN_DURATION_MS / 1000.0

    def jump(self, position: Position):
        """
        מסמן כלי כ-'defending' למשך 3 שניות.
        Extra route: airborne/collision behavior.
        """
        piece = self.board.get_piece_at(position)
        if piece is not None:
            piece.state = DEFENDING
            jump_duration = MOVE_TIME_PER_CELL * 3  # 3 שניות באוויר
            motion = Motion(piece, position, position, jump_duration)
            self._arbiter.set_jump_motion(motion)

            # מאתחל שעון אם צריך
            if self._start_time is None:
                self._start_time = time.time()

            # מוסיף ל-log
            elapsed = time.time() - self._start_time
            self._moves_log.append(MoveLogEntry(
                piece.kind, piece.color, position, position, elapsed
            ))

    def get_active_motion_info(self):
        """מחזיר רשימת תנועות פעילות (למטרות rendering interpolation)."""
        return self._arbiter.get_motion_info()

    def get_promotion_message(self):
        """מחזיר הודעת promotion אם עדיין פעילה, אחרת None."""
        if self._promotion_message is None:
            return None
        msg, expire = self._promotion_message
        if time.time() > expire:
            self._promotion_message = None
            return None
        return msg

    def get_cooldown_info(self):
        """מחזיר dict: piece_id -> progress (0.0=just started, 1.0=about to finish)."""
        now = time.time()
        info = {}
        cooldown_sec = COOLDOWN_DURATION_MS / 1000.0
        for pid, expire in self._resting_pieces.items():
            remaining = expire - now
            if remaining > 0:
                progress = 1.0 - (remaining / cooldown_sec)  # 0=full yellow, 1=transparent
                info[pid] = progress
        return info

    def get_snapshot(self) -> GameSnapshot:
        """מחזיר snapshot read-only למצב הנוכחי."""
        return GameSnapshot(
            self.board, self.state.game_over, self.state.winner,
            self._white_score, self._black_score, list(self._moves_log)
        )
