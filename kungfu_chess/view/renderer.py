"""
שכבה: View / Renderer
renderer.py — מצייר את מצב המשחק על המסך.
מקבל GameSnapshot (read-only). לא משנה game state.
משתמש אך ורק בספריית Img — לא PyGame, לא SFML.
"""
import os
import json
import time

import cv2
import numpy as np

from kungfu_chess.view.img import Img
from kungfu_chess.model.position import Position
from kungfu_chess.model.piece import WHITE, BLACK, IDLE, MOVING, CAPTURED
from kungfu_chess.input.board_mapper import CELL_SIZE
from kungfu_chess.constants import (
    RENDER_CELL_SIZE, SIDE_PANEL_WIDTH, TOP_BAR_HEIGHT, BOTTOM_BAR_HEIGHT,
)


# מיפוי (color, kind) -> שם תיקיית sprites
PIECE_FOLDER_MAP = {
    (WHITE, "king"): "KW",
    (WHITE, "queen"): "QW",
    (WHITE, "rook"): "RW",
    (WHITE, "bishop"): "BW",
    (WHITE, "knight"): "NW",
    (WHITE, "pawn"): "PW",
    (BLACK, "king"): "KB",
    (BLACK, "queen"): "QB",
    (BLACK, "rook"): "RB",
    (BLACK, "bishop"): "BB",
    (BLACK, "knight"): "NB",
    (BLACK, "pawn"): "PB",
}

# State שם -> תיקייה
STATE_FOLDER_MAP = {
    IDLE: "idle",
    MOVING: "move",
    "jump": "jump",
    "short_rest": "short_rest",
    "long_rest": "long_rest",
}


class SpriteAnimation:
    """מנהל אנימציה של sprite — מחליף פריימים לפי FPS."""

    def __init__(self, sprites_dir: str):
        config_path = os.path.join(sprites_dir, "config.json")
        sprites_path = os.path.join(sprites_dir, "sprites")

        with open(config_path, "r") as f:
            config = json.load(f)

        self.fps = config["graphics"]["frames_per_sec"]
        self.is_loop = config["graphics"]["is_loop"]
        self.frame_duration = 1.0 / self.fps if self.fps > 0 else 1.0

        # טוען את כל הפריימים
        self.frames = []
        frame_files = sorted(os.listdir(sprites_path))
        for fname in frame_files:
            if fname.endswith(".png"):
                path = os.path.join(sprites_path, fname)
                sprite = Img().read(path, size=(RENDER_CELL_SIZE, RENDER_CELL_SIZE), keep_aspect=True)
                self.frames.append(sprite)

        self.current_frame = 0
        self.last_frame_time = time.time()

    def get_current_frame(self) -> Img:
        """מחזיר את הפריים הנוכחי ומקדם אם צריך."""
        if not self.frames:
            return None

        now = time.time()
        elapsed = now - self.last_frame_time

        if elapsed >= self.frame_duration:
            if self.is_loop:
                self.current_frame = (self.current_frame + 1) % len(self.frames)
            else:
                if self.current_frame < len(self.frames) - 1:
                    self.current_frame += 1
            self.last_frame_time = now

        return self.frames[self.current_frame]


class Renderer:
    """
    מצייר את מצב המשחק.
    מקבל snapshot + selected cell.
    לא משנה game state — read-only rendering.
    """

    def __init__(self, assets_dir: str, board_image_path: str, idle_assets_dir: str = None):
        """
        assets_dir: תיקיית pieces לתנועה/קפיצה (e.g. CTD26/pieces1)
        board_image_path: נתיב לתמונת הלוח
        idle_assets_dir: תיקיית pieces ל-idle (e.g. CTD26/pieces2). אם None = אותו כמו assets_dir.
        """
        self._assets_dir = assets_dir
        self._idle_assets_dir = idle_assets_dir or assets_dir
        self._board_img_path = board_image_path
        self._animations = {}  # cache: (piece_folder, state) -> SpriteAnimation

    def _get_animation(self, piece_folder: str, state: str) -> SpriteAnimation:
        """מחזיר animation (cached) לפי כלי ומצב."""
        state_folder = STATE_FOLDER_MAP.get(state, "idle")
        key = (piece_folder, state_folder)

        if key not in self._animations:
            # idle משתמש ב-idle_assets_dir, שאר ב-assets_dir
            base_dir = self._idle_assets_dir if state_folder == "idle" else self._assets_dir
            sprites_dir = os.path.join(base_dir, piece_folder, "states", state_folder)
            if os.path.exists(sprites_dir):
                self._animations[key] = SpriteAnimation(sprites_dir)
            else:
                # fallback to idle
                idle_dir = os.path.join(self._idle_assets_dir, piece_folder, "states", "idle")
                self._animations[key] = SpriteAnimation(idle_dir)

        return self._animations[key]

    def render_frame(self, snapshot, selected_pos=None, motion_info=None, promotion_msg=None, cooldown_info=None):
        """
        מצייר frame אחד של המשחק ומחזיר את ה-canvas.
        Layout: [Black moves] [Board] [White moves]
                Name top, Score+Name bottom
        """
        board = snapshot.board

        # גודל תא לציור
        render_cell = RENDER_CELL_SIZE
        board_width = board.cols * render_cell
        board_height = board.rows * render_cell

        # Panel dimensions
        side_panel_width = SIDE_PANEL_WIDTH
        top_bar_height = TOP_BAR_HEIGHT
        bottom_bar_height = BOTTOM_BAR_HEIGHT

        total_width = side_panel_width + board_width + side_panel_width
        total_height = top_bar_height + board_height + bottom_bar_height

        # Create canvas
        canvas = Img()
        canvas.img = np.ones((total_height, total_width, 4), dtype=np.uint8) * 50

        # --- Top bar: player name + score ---
        canvas.put_text("Name: Chicko Miko", total_width // 2 - 70, 22, 0.5,
                        color=(255, 255, 255, 255), thickness=1)
        canvas.put_text(f"Score: {snapshot.black_score}",
                        total_width // 2 + 80, 22, 0.5,
                        color=(200, 200, 255, 255), thickness=1)

        # --- Board ---
        board_x_offset = side_panel_width
        board_y_offset = top_bar_height

        board_img = Img().read(self._board_img_path,
                               size=(board_width, board_height))
        board_img.draw_on(canvas, board_x_offset, board_y_offset)

        # Column letters (a-h)
        col_letters = "abcdefgh"
        for c in range(min(board.cols, 8)):
            cx = board_x_offset + c * render_cell + render_cell // 2 - 5
            canvas.put_text(col_letters[c], cx, board_y_offset + board_height + 15, 0.4,
                            color=(200, 200, 200, 255), thickness=1)

        # Row numbers (8-1, top to bottom)
        for r in range(min(board.rows, 8)):
            ry = board_y_offset + r * render_cell + render_cell // 2 + 5
            canvas.put_text(str(8 - r), board_x_offset - 15, ry, 0.4,
                            color=(200, 200, 200, 255), thickness=1)

        # --- Highlight selected ---
        if selected_pos is not None:
            self._draw_highlight_offset(canvas, selected_pos, board_x_offset, board_y_offset)

        # --- Cooldown overlay (dark yellow fading out) ---
        if cooldown_info is None:
            cooldown_info = {}
        for piece in board.all_pieces():
            if piece.state == "resting" and piece.id in cooldown_info:
                px = board_x_offset + piece.cell.col * render_cell
                py = board_y_offset + piece.cell.row * render_cell
                progress = cooldown_info[piece.id]  # 0=just started, 1=about to finish

                # צהוב כהה — opacity יורד עם הזמן
                # opacity: 180 בהתחלה → 0 בסוף
                opacity = int(180 * (1.0 - progress))
                if opacity > 0:
                    # מצייר מלבן צהוב כהה חצי-שקוף
                    # גובה המלבן יורד — "מתרוקן" מלמעלה למטה
                    fill_height = int(render_cell * (1.0 - progress))
                    if fill_height > 0:
                        y_start = py + (render_cell - fill_height)
                        overlay = canvas.img[y_start:y_start+fill_height, px:px+render_cell].copy()
                        yellow = np.full((fill_height, render_cell, 4), (0, 180, 220, opacity), dtype=np.uint8)
                        alpha = opacity / 255.0
                        for c in range(3):
                            overlay[:, :, c] = ((1 - alpha) * overlay[:, :, c] + alpha * yellow[:, :, c]).astype(np.uint8)
                        canvas.img[y_start:y_start+fill_height, px:px+render_cell] = overlay

        # --- Draw pieces ---
        moving_piece_ids = set()
        if motion_info is not None:
            for mi in motion_info:
                moving_piece_ids.add(mi["piece"].id)

        for piece in board.all_pieces():
            if piece.state == CAPTURED:
                continue
            if piece.id in moving_piece_ids:
                continue

            folder = PIECE_FOLDER_MAP.get((piece.color, piece.kind))
            if folder is None:
                continue

            # כלי שקופץ (DEFENDING) — אנימציית jump + מוגבה
            if piece.state == "defending":
                anim = self._get_animation(folder, "jump")
            else:
                anim = self._get_animation(folder, piece.state)
            frame = anim.get_current_frame()
            if frame is None:
                continue

            px = board_x_offset + piece.cell.col * render_cell
            py = board_y_offset + piece.cell.row * render_cell
            # אם קופץ — מעלה 15px למעלה (אפקט "באוויר")
            if piece.state == "defending":
                py -= 15
            frame.draw_on(canvas, px, py)

        # --- Draw moving pieces (interpolated) ---
        if motion_info is not None:
            for mi in motion_info:
                piece = mi["piece"]
                src = mi["source"]
                dst = mi["destination"]
                progress = mi["progress"]

                folder = PIECE_FOLDER_MAP.get((piece.color, piece.kind))
                if folder:
                    anim = self._get_animation(folder, "jump")
                    frame = anim.get_current_frame()
                    if frame:
                        px = int(board_x_offset + src.col * render_cell +
                                 (dst.col - src.col) * render_cell * progress)
                        py = int(board_y_offset + src.row * render_cell +
                                 (dst.row - src.row) * render_cell * progress)
                        frame.draw_on(canvas, px, py)

        # --- Left panel: Black moves ---
        lx = 5
        canvas.put_text("Black", lx + 20, top_bar_height + 20, 0.5,
                        color=(180, 180, 255, 255), thickness=1)
        canvas.put_text("Time   Move", lx, top_bar_height + 40, 0.35,
                        color=(150, 150, 150, 255), thickness=1)

        black_moves = [m for m in snapshot.moves_log if m.color == "black"]
        for i, move in enumerate(black_moves[-20:]):
            y_pos = top_bar_height + 60 + i * 16
            if y_pos > top_bar_height + board_height - 10:
                break
            canvas.put_text(move.time_str(), lx, y_pos, 0.3,
                            color=(150, 150, 200, 255), thickness=1)
            canvas.put_text(str(move), lx + 80, y_pos, 0.3,
                            color=(220, 220, 255, 255), thickness=1)

        # --- Right panel: White moves ---
        rx = side_panel_width + board_width + 5
        canvas.put_text("White", rx + 20, top_bar_height + 20, 0.5,
                        color=(180, 255, 180, 255), thickness=1)
        canvas.put_text("Time   Move", rx, top_bar_height + 40, 0.35,
                        color=(150, 150, 150, 255), thickness=1)

        white_moves = [m for m in snapshot.moves_log if m.color == "white"]
        for i, move in enumerate(white_moves[-20:]):
            y_pos = top_bar_height + 60 + i * 16
            if y_pos > top_bar_height + board_height - 10:
                break
            canvas.put_text(move.time_str(), rx, y_pos, 0.3,
                            color=(150, 200, 150, 255), thickness=1)
            canvas.put_text(str(move), rx + 80, y_pos, 0.3,
                            color=(220, 255, 220, 255), thickness=1)

        # --- Bottom bar: Score + White player name ---
        score_y = top_bar_height + board_height + 25
        canvas.put_text(f"Score: {snapshot.white_score}",
                        total_width // 2 - 40, score_y, 0.6,
                        color=(255, 255, 255, 255), thickness=2)
        canvas.put_text("Name: Musti Shusti",
                        total_width // 2 - 70, score_y + 30, 0.5,
                        color=(255, 255, 255, 255), thickness=1)

        # --- Game over ---
        if snapshot.game_over:
            winner = "White" if snapshot.winner == WHITE else "Black"
            cx = board_x_offset + board_width // 2 - 120
            cy = board_y_offset + board_height // 2
            canvas.put_text(f"GAME OVER - {winner} wins!",
                            cx, cy, 0.9,
                            color=(0, 0, 255, 255), thickness=3)

        # --- Promotion notification ---
        if promotion_msg:
            cx = board_x_offset + board_width // 2 - 100
            cy = board_y_offset + 20
            canvas.put_text(promotion_msg, cx, cy, 0.5,
                            color=(0, 255, 255, 255), thickness=2)

        return canvas

    def _draw_highlight_offset(self, canvas, pos, x_offset, y_offset, cell_size=RENDER_CELL_SIZE):
        """מצייר highlight עם offset."""
        x = x_offset + pos.col * cell_size
        y = y_offset + pos.row * cell_size
        cv2.rectangle(canvas.img, (x, y), (x + cell_size, y + cell_size),
                      (0, 255, 0, 255), 3)

    def render(self, snapshot, selected_pos=None):
        """מצייר frame ומציג בחלון (לשימוש בודד בלי game loop)."""
        canvas = self.render_frame(snapshot, selected_pos)
        canvas.show()

    def _draw_highlight(self, canvas, pos: Position):
        """מצייר מלבן highlight סביב התא הנבחר."""
        import cv2
        x = pos.col * CELL_SIZE
        y = pos.row * CELL_SIZE
        cv2.rectangle(canvas.img, (x, y), (x + CELL_SIZE, y + CELL_SIZE),
                      (0, 255, 0, 255), 3)
