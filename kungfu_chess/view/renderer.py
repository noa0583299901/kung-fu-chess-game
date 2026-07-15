"""
שכבה: View / Renderer
renderer.py — מצייר את מצב המשחק על המסך.
מקבל GameSnapshot (read-only). לא משנה game state.
משתמש אך ורק בספריית Img — לא PyGame, לא SFML.
"""
import os
import json
import time

from kungfu_chess.view.img import Img
from kungfu_chess.model.position import Position
from kungfu_chess.model.piece import WHITE, BLACK, IDLE, MOVING, CAPTURED
from kungfu_chess.input.board_mapper import CELL_SIZE


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
                sprite = Img().read(path, size=(CELL_SIZE, CELL_SIZE), keep_aspect=True)
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

    def __init__(self, assets_dir: str, board_image_path: str):
        """
        assets_dir: תיקיית pieces (e.g. CTD26/pieces1)
        board_image_path: נתיב לתמונת הלוח (e.g. CTD26/board.png)
        """
        self._assets_dir = assets_dir
        self._board_img_path = board_image_path
        self._animations = {}  # cache: (piece_folder, state) -> SpriteAnimation

    def _get_animation(self, piece_folder: str, state: str) -> SpriteAnimation:
        """מחזיר animation (cached) לפי כלי ומצב."""
        state_folder = STATE_FOLDER_MAP.get(state, "idle")
        key = (piece_folder, state_folder)

        if key not in self._animations:
            sprites_dir = os.path.join(self._assets_dir, piece_folder, "states", state_folder)
            if os.path.exists(sprites_dir):
                self._animations[key] = SpriteAnimation(sprites_dir)
            else:
                # fallback to idle
                idle_dir = os.path.join(self._assets_dir, piece_folder, "states", "idle")
                self._animations[key] = SpriteAnimation(idle_dir)

        return self._animations[key]

    def render_frame(self, snapshot, selected_pos=None, motion_info=None):
        """
        מצייר frame אחד של המשחק ומחזיר את ה-canvas.
        snapshot: GameSnapshot
        selected_pos: Position של הכלי הנבחר (או None)
        motion_info: dict עם piece, source, destination, progress (או None)
        Returns: Img (canvas מוכן להצגה)
        """
        board = snapshot.board
        board_width = board.cols * CELL_SIZE
        board_height = board.rows * CELL_SIZE

        # יוצרים canvas רחב יותר — לוח + פאנל צדדי
        panel_width = 200
        total_width = board_width + panel_width
        import numpy as np
        canvas = Img()
        canvas.img = np.ones((board_height, total_width, 4), dtype=np.uint8) * 40  # רקע כהה

        # טוען תמונת לוח ומציב על ה-canvas
        board_img = Img().read(self._board_img_path,
                               size=(board_width, board_height))
        board_img.draw_on(canvas, 0, 0)

        # מצייר highlight על selected
        if selected_pos is not None:
            self._draw_highlight(canvas, selected_pos)

        # כלי שנמצא בתנועה — נצייר אותו בנפרד (interpolated)
        moving_piece_id = None
        if motion_info is not None:
            moving_piece_id = motion_info["piece"].id

        # מצייר כלים
        for piece in board.all_pieces():
            if piece.state == CAPTURED:
                continue
            # אם הכלי בתנועה — מדלגים, נצייר אותו בנפרד
            if moving_piece_id is not None and piece.id == moving_piece_id:
                continue

            folder = PIECE_FOLDER_MAP.get((piece.color, piece.kind))
            if folder is None:
                continue

            anim = self._get_animation(folder, piece.state)
            frame = anim.get_current_frame()
            if frame is None:
                continue

            # מיקום פיקסל
            px = piece.cell.col * CELL_SIZE
            py = piece.cell.row * CELL_SIZE
            frame.draw_on(canvas, px, py)

        # מצייר את הכלי הנע במיקום interpolated
        if motion_info is not None:
            piece = motion_info["piece"]
            src = motion_info["source"]
            dst = motion_info["destination"]
            progress = motion_info["progress"]

            folder = PIECE_FOLDER_MAP.get((piece.color, piece.kind))
            if folder:
                anim = self._get_animation(folder, MOVING)
                frame = anim.get_current_frame()
                if frame:
                    # interpolation — מיקום ביניים
                    px = int(src.col * CELL_SIZE + (dst.col - src.col) * CELL_SIZE * progress)
                    py = int(src.row * CELL_SIZE + (dst.row - src.row) * CELL_SIZE * progress)
                    frame.draw_on(canvas, px, py)

        # --- פאנל צדדי: score + moves log ---
        panel_x = board_width + 10

        # Score
        canvas.put_text("SCORE", panel_x, 30, 0.7,
                        color=(255, 255, 255, 255), thickness=2)
        canvas.put_text(f"White: {snapshot.white_score}", panel_x, 60, 0.5,
                        color=(200, 200, 200, 255), thickness=1)
        canvas.put_text(f"Black: {snapshot.black_score}", panel_x, 85, 0.5,
                        color=(200, 200, 200, 255), thickness=1)

        # Moves log
        canvas.put_text("MOVES", panel_x, 120, 0.7,
                        color=(255, 255, 255, 255), thickness=2)

        # מציג את 15 המהלכים האחרונים
        recent_moves = snapshot.moves_log[-15:]
        for i, move in enumerate(recent_moves):
            y_pos = 150 + i * 20
            if y_pos > board_height - 20:
                break
            color = (180, 220, 180, 255) if move.color == WHITE else (180, 180, 220, 255)
            canvas.put_text(str(move), panel_x, y_pos, 0.4,
                            color=color, thickness=1)

        # game over message
        if snapshot.game_over:
            winner = "White" if snapshot.winner == WHITE else "Black"
            canvas.put_text(f"GAME OVER", board_width // 2 - 100, board_height // 2 - 20, 1.2,
                            color=(0, 0, 255, 255), thickness=3)
            canvas.put_text(f"{winner} wins!", board_width // 2 - 80, board_height // 2 + 20, 0.8,
                            color=(0, 0, 255, 255), thickness=2)

        return canvas

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
