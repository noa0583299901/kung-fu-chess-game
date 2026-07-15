"""
Entry point גרפי — מפעיל את המשחק עם חלון ציור.
מקבל לוח התחלתי מקובץ טקסט, מציג אותו גרפית,
ומטפל בלחיצות עכבר כ-input.

שכבה: Application (top-level)
תלוי ב: Controller, GameEngine, Renderer, BoardParser
"""
import sys
import os
import cv2
import time

from kungfu_chess.io.board_parser import parse_board
from kungfu_chess.engine.game_engine import GameEngine
from kungfu_chess.input.controller import Controller
from kungfu_chess.input.board_mapper import CELL_SIZE
from kungfu_chess.view.renderer import Renderer
from kungfu_chess.view.img import Img


# --- הגדרות ---
# נתיבים ברירת מחדל (יחסית לתיקיית הפרויקט)
DEFAULT_BOARD = [
    "bR bN bB bQ bK bB bN bR",
    "bP bP bP bP bP bP bP bP",
    ". . . . . . . .",
    ". . . . . . . .",
    ". . . . . . . .",
    ". . . . . . . .",
    "wP wP wP wP wP wP wP wP",
    "wR wN wB wQ wK wB wN wR",
]

# FPS של לולאת המשחק
GAME_FPS = 30
FRAME_DELAY_MS = 1000 // GAME_FPS  # ~33ms per frame


def find_assets_dir():
    """מוצא את תיקיית ה-assets (pieces1) — מחפש ב-CTD26."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ctd26_path = os.path.join(project_root, "CTD26", "pieces1")
    if os.path.exists(ctd26_path):
        return ctd26_path
    # fallback — pieces1 בתיקיה ראשית
    fallback = os.path.join(project_root, "pieces1")
    if os.path.exists(fallback):
        return fallback
    raise FileNotFoundError("Cannot find pieces1 assets directory")


def find_board_image():
    """מוצא את תמונת הלוח."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(project_root, "CTD26", "board.png")
    if os.path.exists(path):
        return path
    fallback = os.path.join(project_root, "board.png")
    if os.path.exists(fallback):
        return fallback
    raise FileNotFoundError("Cannot find board.png")


# --- משתנה גלובלי ללחיצות עכבר ---
_mouse_click = None


def _mouse_callback(event, x, y, flags, param):
    """Callback שמופעל על ידי OpenCV כשלוחצים עם העכבר."""
    global _mouse_click
    if event == cv2.EVENT_LBUTTONDOWN:
        _mouse_click = (x, y)


def main(board_lines=None):
    """
    מפעיל את המשחק הגרפי.
    board_lines: רשימת שורות טקסט להגדרת הלוח (או None לברירת מחדל).
    """
    global _mouse_click

    # --- אתחול ---
    if board_lines is None:
        board_lines = DEFAULT_BOARD

    board, error = parse_board(board_lines)
    if error:
        print(f"Board error: {error}")
        return
    if board is None:
        print("Empty board")
        return

    engine = GameEngine(board)
    controller = Controller(engine)

    assets_dir = find_assets_dir()
    board_img_path = find_board_image()
    renderer = Renderer(assets_dir, board_img_path)

    # --- חלון OpenCV ---
    window_name = "Kung Fu Chess"
    cv2.namedWindow(window_name)
    cv2.setMouseCallback(window_name, _mouse_callback)

    # --- Game loop ---
    last_time = time.time()

    while True:
        # --- Handle input ---
        if _mouse_click is not None:
            x, y = _mouse_click
            _mouse_click = None
            # Adjust click position: subtract board offset
            board_x = x - 160  # side_panel_width
            board_y = y - 30   # top_bar_height
            # Convert render pixels to logical pixels (render_cell=70, CELL_SIZE=100)
            # Cell = board_x // 70, so logical_x = cell * 100 + 50 (center of cell)
            col = board_x // 70
            row = board_y // 70
            logical_x = col * CELL_SIZE + CELL_SIZE // 2
            logical_y = row * CELL_SIZE + CELL_SIZE // 2
            controller.handle_click(logical_x, logical_y)

        # --- Advance time ---
        current_time = time.time()
        elapsed_ms = int((current_time - last_time) * 1000)
        last_time = current_time

        if elapsed_ms > 0:
            engine.wait(elapsed_ms)

        # --- Render ---
        snapshot = engine.get_snapshot()
        motion_info = engine.get_active_motion_info()
        promotion_msg = engine.get_promotion_message()
        canvas = renderer.render_frame(snapshot, controller.selected, motion_info, promotion_msg)

        cv2.imshow(window_name, canvas.img)

        # --- Check quit / keyboard shortcuts ---
        key = cv2.waitKey(FRAME_DELAY_MS) & 0xFF
        if key == 27 or key == ord('q'):  # ESC or Q to quit
            break
        elif key == ord('r'):  # R to reset
            board, _ = parse_board(board_lines)
            engine = GameEngine(board)
            controller = Controller(engine)

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
