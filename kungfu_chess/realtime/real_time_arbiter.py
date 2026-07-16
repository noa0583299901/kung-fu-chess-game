"""
שכבה: RealTimeArbiter
real_time_arbiter.py — מנהל תנועות פעילות.
מקדם elapsed time, מזהה arrival, ומדווח על capture events.
תומך במספר תנועות במקביל (Kung Fu Chess).
לא יודע על חוקי שחמט, clicks, rendering, או script parsing.
"""
from kungfu_chess.model.board import Board
from kungfu_chess.model.piece import Piece, KING, MOVING, IDLE, DEFENDING
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
        self._active_motions = []  # רשימה של Motion — מספר תנועות במקביל
        self._jump_motion = None

    @property
    def has_active_motion(self) -> bool:
        return len(self._active_motions) > 0

    def is_piece_moving(self, piece_id: int) -> bool:
        """בודק אם כלי ספציפי כבר בתנועה."""
        return any(m.piece.id == piece_id for m in self._active_motions)

    def get_motion_info(self):
        """מחזיר מידע על כל התנועות הפעילות (למטרות rendering)."""
        if not self._active_motions:
            return None
        # מחזיר רשימה של כל התנועות
        infos = []
        for motion in self._active_motions:
            progress = motion.elapsed / motion.duration if motion.duration > 0 else 1.0
            infos.append({
                "piece": motion.piece,
                "source": motion.source,
                "destination": motion.destination,
                "progress": min(progress, 1.0),
            })
        return infos

    def set_jump_motion(self, motion: Motion):
        """מגדיר jump motion (defending state with timeout)."""
        self._jump_motion = motion

    def start_motion(self, piece: Piece, destination: Position) -> Motion:
        """
        מתחיל תנועה חדשה. מוסיף לרשימת התנועות הפעילות.
        """
        source = piece.cell
        duration = calculate_duration(piece, source, destination)
        motion = Motion(piece, source, destination, duration)
        piece.state = MOVING
        self._active_motions.append(motion)
        return motion

    def advance_time(self, milliseconds: int, board: Board):
        """
        מקדם את הזמן לכל התנועות. מחזיר רשימת ArrivalEvents (או None).
        """
        # מקדם jump motion
        if self._jump_motion is not None:
            self._jump_motion.advance(milliseconds)
            if self._jump_motion.finished:
                self._jump_motion.piece.state = IDLE
                self._jump_motion = None

        if not self._active_motions:
            return None

        # מקדם את כל התנועות
        for motion in self._active_motions:
            motion.advance(milliseconds)

        # בודק מי הגיע — ממוין לפי מי שהתחיל קודם (elapsed גבוה = התחיל מוקדם יותר)
        arrived = [m for m in self._active_motions if m.finished]
        if not arrived:
            return None

        # ממיין: מי שצבר יותר elapsed time (= התחיל לנוע קודם) מגיע ראשון
        arrived.sort(key=lambda m: m.elapsed, reverse=True)

        # מטפל בכל ה-arrivals
        events = []
        occupied_destinations = set()  # תאים שכבר נתפסו ב-frame הזה

        for motion in arrived:
            self._active_motions.remove(motion)

            # בדיקה: האם תא היעד כבר נתפס ב-arrival אחר בframe הזה?
            if motion.destination in occupied_destinations:
                # collision — כלי חוזר למקומו
                motion.piece.state = IDLE
                continue

            # בדיקה: האם כלי אחר (שהגיע קודם) כבר נמצא ביעד?
            existing = board.get_piece_at(motion.destination)
            if existing is not None and existing.color == motion.piece.color and existing.state != DEFENDING:
                # אותו צבע — כלי חוזר למקומו
                motion.piece.state = IDLE
                continue

            event = self._resolve_arrival(motion, board)
            if event is not None:
                events.append(event)
                occupied_destinations.add(motion.destination)

        return events if events else None

    def _resolve_arrival(self, motion: Motion, board: Board):
        """מטפל ב-arrival בודד — collision, capture, placement."""
        # בדיקת collision עם כלי מגן
        defender = board.get_piece_at(motion.destination)
        if defender is not None and defender.state == DEFENDING:
            board.remove_piece(motion.source)
            motion.piece.state = "captured"
            defender.state = IDLE
            return ArrivalEvent(defender, motion.destination, motion.piece)

        # arrival רגיל
        captured = board.move_piece(motion.source, motion.destination)
        motion.piece.state = IDLE
        return ArrivalEvent(motion.piece, motion.destination, captured)
