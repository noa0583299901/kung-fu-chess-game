"""
Kung Fu Chess — GUI Client (Online multiplayer)

מחבר את ה-GUI (renderer + animations) לServer דרך WebSocket.
במקום GameEngine מקומי — שולח clicks לServer ומקבל state בחזרה.

שימוש:
    python app_gui_online.py

מהלך:
    1. Login (username + password)
    2. Play / Room Create / Room Join
    3. חלון גרפי — clicks נשלחים לServer, state מצויר
"""
import asyncio
import json
import time
import threading
import cv2
import websockets

from kungfu_chess.view.renderer import Renderer
from kungfu_chess.view.img import Img
from kungfu_chess.model.position import Position
from kungfu_chess.io.board_parser import parse_board
from kungfu_chess.io.board_printer import board_to_string
from kungfu_chess.engine.game_engine import GameEngine, GameSnapshot
from kungfu_chess.model.board import Board
from kungfu_chess.constants import RENDER_CELL_SIZE, SIDE_PANEL_WIDTH, TOP_BAR_HEIGHT
from kungfu_chess.input.board_mapper import CELL_SIZE

SERVER_URL = "ws://localhost:8765"
GAME_FPS = 30
FRAME_DELAY_MS = 1000 // GAME_FPS

# --- State שה-GUI צריך ---
current_state = None        # dict עם board, scores, game_over...
my_color = None             # "white" / "black" / "viewer"
game_started = False
connected = False
ws_connection = None        # WebSocket connection


# ===========================================================================
# WebSocket — רץ ב-thread נפרד
# ===========================================================================

async def ws_loop(action, username, password, lobby_choice, room_id_input):
    """מתחבר לServer, שולח login, ומקבל state updates."""
    global current_state, my_color, game_started, connected, ws_connection

    print(f"\nConnecting to {SERVER_URL}...")

    async with websockets.connect(SERVER_URL) as ws:
        ws_connection = ws
        connected = True

        # שולח login
        await ws.send(json.dumps({
            "type": action,
            "username": username,
            "password": password,
        }))

        # מחכה לתגובה
        response = json.loads(await ws.recv())
        if response.get("type") == "error":
            print(f"Error: {response['message']}")
            return
        print(f"✓ Logged in! Rating: {response.get('rating', '?')}")

        # --- Lobby action ---
        if lobby_choice == "1":
            await ws.send(json.dumps({"type": "play"}))
            print("⏳ Searching for opponent...")
        elif lobby_choice == "2":
            await ws.send(json.dumps({"type": "create_room"}))
            resp = json.loads(await ws.recv())
            if resp.get("type") == "room_created":
                print(f"✓ Room created! ID: {resp['room_id']}")
                print("Waiting for opponent...")
            elif resp.get("type") == "error":
                print(f"Error: {resp['message']}")
                return
        elif lobby_choice == "3":
            await ws.send(json.dumps({"type": "join_room", "room_id": room_id_input}))

        # --- מקבל messages ---
        async for message in ws:
            data = json.loads(message)
            msg_type = data.get("type")

            if msg_type == "game_start":
                my_color = data.get("color", "viewer")
                game_started = True
                print(f"\n🎮 Game started! You are: {my_color.upper()}")
                print(f"   Opponent: {data.get('opponent', '?')}")

            elif msg_type == "state":
                current_state = data.get("data")

            elif msg_type == "viewer":
                my_color = "viewer"
                game_started = True
                print("👁 You are a viewer")

            elif msg_type == "searching":
                print(f"⏳ {data.get('message', '')}")

            elif msg_type == "matchmaking_failed":
                print(f"✗ {data.get('message', '')}")
                return

            elif msg_type == "opponent_disconnected":
                print(f"⚠ Opponent disconnected! {data['countdown']}s countdown")

            elif msg_type == "opponent_resigned":
                print(f"🏆 {data.get('message', '')}")

            elif msg_type == "rejected":
                pass

            elif msg_type == "error":
                print(f"Error: {data.get('message', '')}")


def start_ws_thread(action, username, password, lobby_choice, room_id_input):
    """מפעיל את WebSocket loop ב-thread נפרד."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(ws_loop(action, username, password, lobby_choice, room_id_input))


# ===========================================================================
# Send move to Server
# ===========================================================================

def send_move(source_pos, dest_pos):
    """שולח מהלך לServer. ממיר Position ל-string format."""
    if ws_connection is None or my_color == "viewer":
        return

    col_letters = "abcdefgh"
    color_letter = "W" if my_color == "white" else "B"

    src_col = col_letters[source_pos.col] if source_pos.col < 8 else "a"
    src_row = str(8 - source_pos.row)
    dst_col = col_letters[dest_pos.col] if dest_pos.col < 8 else "a"
    dst_row = str(8 - dest_pos.row)

    # פורמט: WRa1a5 — אבל אנחנו לא יודעים את סוג הכלי, אז נשתמש ב-X כplaceholder
    # Server ממילא משתמש ב-source position למציאת הכלי
    cmd = f"{color_letter}X{src_col}{src_row}{dst_col}{dst_row}"

    asyncio.run_coroutine_threadsafe(
        ws_connection.send(json.dumps({"type": "move", "cmd": cmd})),
        asyncio.get_event_loop()
    )


def send_jump(position):
    """שולח jump לServer."""
    if ws_connection is None or my_color == "viewer":
        return

    col_letters = "abcdefgh"
    color_letter = "W" if my_color == "white" else "B"
    col = col_letters[position.col] if position.col < 8 else "a"
    row = str(8 - position.row)
    cmd = f"JUMP {color_letter}P{col}{row}"

    asyncio.run_coroutine_threadsafe(
        ws_connection.send(json.dumps({"type": "jump", "cmd": cmd})),
        asyncio.get_event_loop()
    )


# ===========================================================================
# GUI — game window
# ===========================================================================

def find_assets():
    """מוצא assets."""
    import os
    project_root = os.path.dirname(os.path.abspath(__file__))
    assets = os.path.join(project_root, "CTD26", "pieces1")
    board_img = os.path.join(project_root, "CTD26", "board.png")
    return assets, board_img


def build_snapshot_from_state(state_dict):
    """ממיר state dict (מServer) ל-objects שRenderer מבין."""
    if state_dict is None:
        return None

    board_text = state_dict.get("board", "")
    lines = board_text.strip().split("\n")
    board, _ = parse_board(lines)
    if board is None:
        return None

    return GameSnapshot(
        board=board,
        game_over=state_dict.get("game_over", False),
        winner=state_dict.get("winner"),
        white_score=state_dict.get("white_score", 0),
        black_score=state_dict.get("black_score", 0),
        moves_log=[],
    )


def gui_main():
    """לולאת ה-GUI — מציגה את ה-state שמגיע מServer."""
    global current_state

    assets_dir, board_img_path = find_assets()
    renderer = Renderer(assets_dir, board_img_path)

    window_name = "Kung Fu Chess — Online"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    selected_pos = None
    mouse_click = None

    def on_mouse(event, x, y, flags, param):
        nonlocal mouse_click
        if event == cv2.EVENT_LBUTTONDOWN:
            mouse_click = (x, y)

    cv2.setMouseCallback(window_name, on_mouse)

    # מחכה שהמשחק יתחיל
    print("\n[GUI] Waiting for game to start...")
    while not game_started:
        time.sleep(0.1)
    print("[GUI] Game window open!")

    while True:
        # --- Handle click ---
        if mouse_click is not None:
            x, y = mouse_click
            mouse_click = None

            board_x = x - SIDE_PANEL_WIDTH
            board_y = y - TOP_BAR_HEIGHT
            col = board_x // RENDER_CELL_SIZE
            row = board_y // RENDER_CELL_SIZE
            pos = Position(row, col)

            if selected_pos is None:
                selected_pos = pos
            else:
                if pos == selected_pos:
                    # double click — jump
                    send_jump(pos)
                    selected_pos = None
                else:
                    # second click — move
                    send_move(selected_pos, pos)
                    selected_pos = None

        # --- Render ---
        snapshot = build_snapshot_from_state(current_state)
        if snapshot is not None:
            canvas = renderer.render_frame(snapshot, selected_pos, None, None, None)
            cv2.imshow(window_name, canvas.img)

        # --- Keyboard ---
        key = cv2.waitKey(FRAME_DELAY_MS) & 0xFF
        if key == 27 or key == ord('q'):
            break

    cv2.destroyAllWindows()


# ===========================================================================
# Main
# ===========================================================================

if __name__ == "__main__":
    # שלב 1: Login + Lobby בטרמינל (לפני GUI)
    print("=" * 40)
    print("   KUNG FU CHESS — ONLINE")
    print("=" * 40)
    print("\n1. Login")
    print("2. Register")
    choice = input("Choice (1/2): ").strip()
    username = input("Username: ").strip()
    password = input("Password: ").strip()
    action = "register" if choice == "2" else "login"

    print("\n1 — Play (matchmaking)")
    print("2 — Create room")
    print("3 — Join room")
    lobby_choice = input("Choice: ").strip()
    room_id_input = ""
    if lobby_choice == "3":
        room_id_input = input("Room ID: ").strip()

    # שלב 2: מפעיל WebSocket עם הפרטים שהוזנו
    import functools
    ws_thread = threading.Thread(
        target=start_ws_thread,
        args=(action, username, password, lobby_choice, room_id_input),
        daemon=True
    )
    ws_thread.start()

    # שלב 3: מפעיל GUI (מחכה שהמשחק יתחיל)
    gui_main()
