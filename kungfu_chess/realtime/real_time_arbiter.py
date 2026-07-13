"""
שכבה: RealTimeArbiter
real_time_arbiter.py — מנהל תנועות פעילות.
מקדם elapsed time, מזהה arrival, ומדווח על capture events.
לא יודע על חוקי שחמט, clicks, rendering, או script parsing.
"""
from kungfu_chess.model.board import Board
from kungfu_chess.model.piece import Piece, KING, MOVING, IDLE

# Piece states extended for jump/defend
DEFENDING = "defending"
from kungfu_chess.model.position import Position
from kungfu_chess.realtime.motion import Motion, calculate_duration


class ArrivalEvent:
    """אירוע — כלי הגיע ליעד."""
    def __init__(self, piece: Piece, destination: Position, captured_piece=None):
        self.piece = piece
        self.destination = destination
        self.captured_piece = captured_piece

    @property
    def king_captured(self) -> bool:
        return self.captured_piece is not None and self.captured_piece.kind == KING


class RealTimeArbiter:
    def __init__(self):
        self._active_motion = None

    @property
    def has_active_motion(self) -> bool:
        return self._active_motion is not None

    def start_motion(self, piece: Piece, destination: Position) -> Motion:
        """
        מתחיל תנועה חדשה. מחזיר את אובייקט ה-Motion.
        Common route: רק תנועה אחת פעילה בו-זמנית.
        """
        source = piece.cell
        duration = calculate_duration(piece, source, destination)
        motion = Motion(piece, source, destination, duration)
        piece.state = MOVING
        self._active_motion = motion
        return motion

    def advance_time(self, milliseconds: int, board: Board):
        """
        מקדם את הזמן. אם תנועה מסתיימת — מבצע arrival ומחזיר ArrivalEvent.
        אם לא סיימה — מחזיר None.
        """
        if self._active_motion is None:
            return None

        motion = self._active_motion
        motion.advance(milliseconds)

        if not motion.finished:
            return None

        # תנועה הסתיימה — בדיקת collision עם כלי מגן
        defender = board.get_piece_at(motion.destination)
        if defender is not None and defender.state == DEFENDING:
            # הכלי המגן אוכל את המגיע
            board.remove_piece(motion.source)  # מסיר את הכלי הנע מהמקור
            motion.piece.state = "captured"
            defender.state = IDLE
            self._active_motion = None
            return ArrivalEvent(defender, motion.destination, motion.piece)

        # arrival רגיל
        captured = board.move_piece(motion.source, motion.destination)
        motion.piece.state = IDLE
        self._active_motion = None

        return ArrivalEvent(motion.piece, motion.destination, captured)
