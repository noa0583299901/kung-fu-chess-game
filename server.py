"""
Kung Fu Chess — WebSocket Server

מריץ את הלוגיקה (GameEngine).
שני Clients מתחברים ושולחים פקודות.
Server שולח מצב לוח מעודכן לשניהם.

פורמט פקודה מ-Client:
    "WRa1a5" = White Rook from a1 to a5
    "BPe7e5" = Black Pawn from e7 to e5
    "JUMP WPe2" = White Pawn at e2 jumps

פורמט תגובה מ-Server:
    JSON עם מצב הלוח המלא
"""
import asyncio
import json
import websockets
import time

from kungfu_chess.io.board_parser import parse_board
from kungfu_chess.io.board_printer import board_to_string
from kungfu_chess.engine.game_engine import GameEngine
from kungfu_chess.engine.event_bus import EventBus
from kungfu_chess.model.position import Position
from kungfu_chess.model.piece import WHITE, BLACK
from database import Database

# --- הגדרות ---
HOST = "localhost"
PORT = 8765

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

# --- שחקנים מחוברים ---
players = {}  # websocket -> {"color": ..., "name": ..., "username": ...}
engine = None
bus = None
game_start_time = None
db = Database()


# ===========================================================================
# Parse command
# ===========================================================================

def parse_command(cmd: str):
    """
    מפרסר פקודה מ-Client.
    "WRa1a5" -> (color, kind, source_pos, dest_pos)
    "JUMP WPe2" -> ("jump", position)
    """
    cmd = cmd.strip()

    if cmd.startswith("JUMP"):
        # JUMP WPe2
        parts = cmd.split()
        if len(parts) == 2:
            piece_str = parts[1]
            color = "white" if piece_str[0] == "W" else "black"
            col = ord(piece_str[2]) - ord('a')
            row = 8 - int(piece_str[3])
            return "jump", Position(row, col)
        return None, None

    if len(cmd) == 6:
        # WRa1a5
        color = "white" if cmd[0] == "W" else "black"
        # source
        src_col = ord(cmd[2]) - ord('a')
        src_row = 8 - int(cmd[3])
        # destination
        dst_col = ord(cmd[4]) - ord('a')
        dst_row = 8 - int(cmd[5])
        return "move", (Position(src_row, src_col), Position(dst_row, dst_col))

    return None, None


# ===========================================================================
# Game state → JSON
# ===========================================================================

def get_game_state_json():
    """מחזיר את מצב המשחק כ-JSON string."""
    snapshot = engine.get_snapshot()
    board_text = board_to_string(snapshot.board)

    state = {
        "board": board_text,
        "game_over": snapshot.game_over,
        "winner": snapshot.winner,
        "white_score": snapshot.white_score,
        "black_score": snapshot.black_score,
        "timestamp": time.time() - game_start_time if game_start_time else 0,
    }
    return json.dumps(state)


# ===========================================================================
# Handle client
# ===========================================================================

async def handle_client(websocket):
    """מטפל בחיבור של client חדש."""
    global game_start_time

    # מחכה להודעת login/register
    try:
        first_msg = await websocket.recv()
        login_data = json.loads(first_msg)
        msg_type = login_data.get("type")
        username = login_data.get("username", "")
        password = login_data.get("password", "")

        if msg_type == "register":
            if db.register(username, password):
                print(f"[SERVER] New user registered: {username}")
            else:
                await websocket.send(json.dumps({"type": "error", "message": "Username already exists"}))
                await websocket.close()
                return
        elif msg_type == "login":
            if not db.login(username, password):
                # אם המשתמש לא קיים — נרשם אוטומטית
                if not db.user_exists(username):
                    db.register(username, password)
                    print(f"[SERVER] Auto-registered: {username}")
                else:
                    await websocket.send(json.dumps({"type": "error", "message": "Wrong password"}))
                    await websocket.close()
                    return
        else:
            await websocket.send(json.dumps({"type": "error", "message": "Expected login or register"}))
            await websocket.close()
            return

        player_name = username
        player_rating = db.get_rating(username)
    except:
        await websocket.close()
        return

    # רישום שחקן — ראשון לבן, שני שחור
    if len(players) == 0:
        players[websocket] = {"color": "white", "name": player_name, "username": username}
        await websocket.send(json.dumps({
            "type": "assigned", "color": "white", "name": player_name, "rating": player_rating
        }))
        print(f"[SERVER] {player_name} (Rating: {player_rating}) connected as White")
        print("[SERVER] Waiting for second player...")
    elif len(players) == 1:
        players[websocket] = {"color": "black", "name": player_name, "username": username}
        await websocket.send(json.dumps({
            "type": "assigned", "color": "black", "name": player_name, "rating": player_rating
        }))
        print(f"[SERVER] {player_name} (Rating: {player_rating}) connected as Black")

        # שני שחקנים — שולח מצב התחלתי
        game_start_time = time.time()
        # שולח שמות שניהם לשניהם
        white_name = [p["name"] for p in players.values() if p["color"] == "white"][0]
        black_name = [p["name"] for p in players.values() if p["color"] == "black"][0]
        for ws in players:
            await ws.send(json.dumps({
                "type": "game_start",
                "white_name": white_name,
                "black_name": black_name,
            }))
        state = get_game_state_json()
        for ws in players:
            await ws.send(json.dumps({"type": "state", "data": json.loads(state)}))
        print(f"[SERVER] Game started! {white_name} (W) vs {black_name} (B)")
    else:
        await websocket.send(json.dumps({"type": "error", "message": "Game full"}))
        await websocket.close()
        return

    try:
        async for message in websocket:
            player_color = players.get(websocket, {}).get("color")

            cmd_type, data = parse_command(message)

            if cmd_type == "move":
                source, dest = data
                result = engine.request_move(source, dest)
                if result.is_accepted:
                    print(f"[SERVER] {player_color}: move accepted {message}")
                else:
                    await websocket.send(json.dumps({
                        "type": "rejected", "reason": result.reason
                    }))
                    continue

            elif cmd_type == "jump":
                position = data
                engine.jump(position)
                print(f"[SERVER] {player_color}: jump at {position}")

            else:
                await websocket.send(json.dumps({
                    "type": "error", "message": "Invalid command"
                }))
                continue

            # שולח מצב מעודכן לשני השחקנים
            state = get_game_state_json()
            for ws in players:
                await ws.send(json.dumps({"type": "state", "data": json.loads(state)}))

    except websockets.exceptions.ConnectionClosed:
        player_info = players.get(websocket, {})
        print(f"[SERVER] {player_info.get('name', 'unknown')} ({player_info.get('color', '?')}) disconnected")
    finally:
        if websocket in players:
            del players[websocket]


# ===========================================================================
# Time advancement (game loop on server)
# ===========================================================================

async def game_tick():
    """מקדם זמן כל 33ms (30 FPS) ושולח עדכונים אם יש שינוי."""
    global game_start_time
    last_time = time.time()

    while True:
        await asyncio.sleep(0.033)  # ~30 FPS

        if engine is None or len(players) < 2:
            continue

        current_time = time.time()
        elapsed_ms = int((current_time - last_time) * 1000)
        last_time = current_time

        if elapsed_ms > 0:
            events = engine.wait(elapsed_ms)
            if events:
                # בודק אם game over — מעדכן ELO
                snapshot = engine.get_snapshot()
                if snapshot.game_over and snapshot.winner:
                    winner_username = None
                    loser_username = None
                    for info in players.values():
                        if info["color"] == snapshot.winner:
                            winner_username = info["username"]
                        else:
                            loser_username = info["username"]
                    if winner_username and loser_username:
                        new_w, new_l = db.update_ratings(winner_username, loser_username)
                        print(f"[SERVER] ELO updated: {winner_username}={new_w}, {loser_username}={new_l}")

                # שולח מצב מעודכן
                state = get_game_state_json()
                for ws in list(players.keys()):
                    try:
                        await ws.send(json.dumps({"type": "state", "data": json.loads(state)}))
                    except:
                        pass


# ===========================================================================
# Main
# ===========================================================================

async def main():
    global engine, bus

    # יוצר את המשחק
    board, error = parse_board(DEFAULT_BOARD)
    if error:
        print(f"Board error: {error}")
        return

    bus = EventBus()
    engine = GameEngine(board, bus=bus)

    print(f"[SERVER] Kung Fu Chess server running on ws://{HOST}:{PORT}")
    print("[SERVER] Waiting for 2 players...")

    # מריץ את ה-tick ברקע
    asyncio.create_task(game_tick())

    # מריץ שרת WebSocket
    async with websockets.serve(handle_client, HOST, PORT):
        await asyncio.Future()  # רץ לנצח


if __name__ == "__main__":
    asyncio.run(main())
