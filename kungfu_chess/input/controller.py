"""
שכבה: Controller
controller.py — מפרש לחיצות ומנהל selected-cell state.
תלוי ב-BoardMapper ו-GameEngine.
לא מכיל: חוקי שחמט, Board mutation, rendering, או timing.
לא קורא ל-Board.move_piece ישירות, ולא ל-RuleEngine ישירות.

Selection policy (fixed):
- First click on a piece: select it.
- First click on empty cell: ignore.
- Second click (in-board): call GameEngine.request_move, then clear selection.
- Outside-board click when no selection: ignore.
- Outside-board click when selection exists: cancel selection, no command.
"""
from kungfu_chess.model.position import Position
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
        # קואורדינטות שליליות — מחוץ ללוח
        if x < 0 or y < 0:
            if self._selected_pos is not None:
                # outside-board click cancels selection
                self._selected_pos = None
            return

        board = self._engine.board
        pos = pixel_to_position(x, y)

        # מחוץ ללוח
        if not board.is_inside(pos):
            if self._selected_pos is not None:
                # outside-board click cancels selection, no command
                self._selected_pos = None
            return

        # --- In-board click ---

        # אין כלי נבחר (first click)
        if self._selected_pos is None:
            piece_at_pos = board.get_piece_at(pos)
            if piece_at_pos is not None:
                self._selected_pos = pos
            # click on empty cell: ignore
            return

        # יש כלי נבחר (second click) — שולח source + destination ומנקה selection
        self._engine.request_move(self._selected_pos, pos)

        # Clear selection after every second in-board click
        self._selected_pos = None
