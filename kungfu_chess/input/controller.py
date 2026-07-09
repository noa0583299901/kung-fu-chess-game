"""
שכבה: Controller
controller.py — מפרש לחיצות ומנהל selected-cell state.
תלוי ב-BoardMapper ו-GameEngine.
לא מכיל: חוקי שחמט, Board mutation, rendering, או timing.
"""
from kungfu_chess.model.position import Position
from kungfu_chess.model.board import Board
from kungfu_chess.model.piece import Piece
from kungfu_chess.engine.game_engine import GameEngine
from kungfu_chess.input.board_mapper import pixel_to_position


class Controller:
    def __init__(self, engine: GameEngine):
        self._engine = engine
        self._selected_pos = None

    @property
    def selected(self):
        return self._selected_pos

    def handle_click(self, x: int, y: int):
        """
        מטפל בלחיצה. מנהל selected state ושולח מהלך ל-engine כשצריך.
        """
        # קואורדינטות שליליות — מתעלם
        if x < 0 or y < 0:
            return

        # game over — מתעלם
        if self._engine.game_over:
            return

        # תנועה פעילה — מתעלם מכל לחיצה
        if self._engine.motion_in_progress:
            return

        board = self._engine.board
        pos = pixel_to_position(x, y)

        # מחוץ ללוח
        if not board.is_inside(pos):
            return

        piece_at_pos = board.get_piece_at(pos)

        # אין כלי נבחר — בוחרים
        if self._selected_pos is None:
            if piece_at_pos is not None:
                self._selected_pos = pos
            return

        # יש כלי נבחר — בודקים מה לעשות עם הלחיצה החדשה
        selected_piece = board.get_piece_at(self._selected_pos)

        # הכלי הנבחר כבר לא קיים (מקרה קצה)
        if selected_piece is None:
            self._selected_pos = None
            return

        # לחיצה על כלי אותו צבע — מחליפים בחירה
        if piece_at_pos is not None and piece_at_pos.color == selected_piece.color:
            self._selected_pos = pos
            return

        # ניסיון מהלך — שולח ל-engine
        response = self._engine.request_move(selected_piece, pos)

        # בכל מקרה — מבטלים בחירה
        self._selected_pos = None
