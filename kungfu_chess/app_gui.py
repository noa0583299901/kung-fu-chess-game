"""
Entry point גרפי — מפעיל את המשחק עם חלון ציור.

שכבה: Application (top-level)
תלוי ב: Controller, GameEngine, Renderer, BoardParser

Controls:
    Mouse click — select piece / send move / double-click to jump
    R — reset game
    ESC / Q — quit
"""
import os
import cv2
import time

from kungfu_chess.io.board_parser import parse_board
from kungfu_chess.engine.game_engine import GameEngine
from kungfu_chess.input.controller import Controller
from kungfu_chess.input.board_mapper import CELL_SIZE
from kungfu_chess.view.renderer import Renderer
from kungfu_chess.constants import RENDER_CELL_SIZE, SIDE_PANEL_WIDTH, TOP_BAR_HEIGHT

# --- לוח ברירת מחדל (שחמט סטנדרטי) ---
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
FRAME_DELAY_MS = 1000 // GAME_FPS

# --- Mouse state ---
_mouse_click = None


def _mouse_callback(event, x, y, flags, param):
    """Callback שמופעל על ידי OpenCV כשלוחצים עם העכבר."""
    global _mouse_click
    if event == cv2.EVENT_LBUTTONDOWN:
        _mouse_click = (x, y)


# ===========================================================================
# Asset discovery
# ===========================================================================

def _find_assets_dir():
    """מוצא את תיקיית ה-sprites."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ctd26_path = os.path.join(project_root, "CTD26", "pieces1")
    if os.path.exists(ctd26_path):
        return ctd26_path
    fallback = os.path.join(project_root, "pieces1")
    if os.path.exists(fallback):
        return fallback
    raise FileNotFoundError("Cannot find pieces1 assets directory")


def _find_board_image():
    """מוצא את תמונת הלוח."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(project_root, "CTD26", "board.png")
    if os.path.exists(path):
        return path
    fallback = os.path.join(project_root, "board.png")
    if os.path.exists(fallback):
        return fallback
    raise FileNotFoundError("Cannot find board.png")


# ===========================================================================
# Game initialization
# ===========================================================================

def _create_game(board_lines):
    """יוצר engine + controller מ-board lines."""
    board, error = parse_board(board_lines)
    if error:
        print(f"Board error: {error}")
        return None, None
    if board is None:
        print("Empty board")
        return None, None
    engine = GameEngine(board)
    controller = Controller(engine)
    return engine, controller


# ===========================================================================
# Input handling
# ===========================================================================

def _handle_mouse_input(controller):
    """מטפל בלחיצת עכבר — מתרגם pixel ל-logical ושולח ל-controller."""
    global _mouse_click
    if _mouse_click is None:
        return

    x, y = _mouse_click
    _mouse_click = None

    # תרגום: pixel → board cell → logical coordinates
    board_x = x - SIDE_PANEL_WIDTH
    board_y = y - TOP_BAR_HEIGHT
    col = board_x // RENDER_CELL_SIZE
    row = board_y // RENDER_CELL_SIZE
    logical_x = col * CELL_SIZE + CELL_SIZE // 2
    logical_y = row * CELL_SIZE + CELL_SIZE // 2

    controller.handle_click(logical_x, logical_y)


# ===========================================================================
# Game loop
# ===========================================================================

def _game_loop(engine, controller, renderer, board_lines):
    """לולאת המשחק הראשית — input, time, render, repeat."""
    window_name = "Kung Fu Chess"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    cv2.setMouseCallback(window_name, _mouse_callback)

    last_time = time.time()

    while True:
        # --- Input ---
        _handle_mouse_input(controller)

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
        cooldown_info = engine.get_cooldown_info()
        canvas = renderer.render_frame(
            snapshot, controller.selected, motion_info, promotion_msg, cooldown_info
        )
        cv2.imshow(window_name, canvas.img)

        # --- Keyboard ---
        key = cv2.waitKey(FRAME_DELAY_MS) & 0xFF
        if key == 27 or key == ord('q'):
            break
        elif key == ord('r'):
            engine, controller = _create_game(board_lines)

    cv2.destroyAllWindows()


# ===========================================================================
# Entry point
# ===========================================================================

def main(board_lines=None):
    """מפעיל את המשחק הגרפי."""
    if board_lines is None:
        board_lines = DEFAULT_BOARD

    engine, controller = _create_game(board_lines)
    if engine is None:
        return

    renderer = Renderer(_find_assets_dir(), _find_board_image())
    _game_loop(engine, controller, renderer, board_lines)


if __name__ == "__main__":
    main()
