"""
Kung Fu Chess — WebSocket Server (Single-process)

Features:
- Login/Register with SQLite + password hash
- Matchmaking: finds opponent with ELO ±100, waits up to 60s
- Disconnect timeout: 20s countdown, then auto-resign
- Real-time game loop with GameEngine

Commands from Client:
    {"type": "login/register", "username": ..., "password": ...}
    {"type": "play"}           — enters matchmaking queue
    {"type": "move", "cmd": "WRa1a5"}
    {"type": "jump", "cmd": "JUMP WPe2"}
"""
import asyncio
import json
import websockets
import time
import logging
import uuid

from kungfu_chess.io.board_parser import parse_board
from kungfu_chess.io.board_printer import board_to_string
from kungfu_chess.engine.game_engine import GameEngine
from kungfu_chess.engine.event_bus import EventBus
from kungfu_chess.model.position import Position
from kungfu_chess.model.piece import WHITE, BLACK
from database import Database

# --- Logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [SERVER] %(message)s",
    handlers=[
        logging.FileHandler("server.log", encoding="utf-8"),
        logging.StreamHandler(),
    ]
)
logger = logging.getLogger("server")

# --- הגדרות ---
HOST = "localhost"
PORT = 8765
MATCHMAKING_TIMEOUT = 60    # שניות לחיפוש יריב
DISCONNECT_TIMEOUT = 20     # שניות לפני auto-resign
ELO_RANGE = 100             # טווח ELO לchיפוש

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

# --- State ---
db = Database()
matchmaking_queue = []  # list of {"ws": websocket, "username": ..., "rating": ..., "time": ...}
active_games = {}       # game_id -> GameSession
rooms = {}              # room_id -> Room


class GameSession:
    """מייצג משחק פעיל בין שני שחקנים."""

    def __init__(self, game_id, white_ws, black_ws, white_user, black_user):
        self.game_id = game_id
        self.white_ws = white_ws
        self.black_ws = black_ws
        self.white_user = white_user
        self.black_user = black_user

        # יוצר engine
        board, _ = parse_board(DEFAULT_BOARD)
        self.bus = EventBus()
        self.engine = GameEngine(board, bus=self.bus)
        self.start_time = time.time()

        # disconnect tracking
        self.disconnected_player = None  # "white" / "black" / None
        self.disconnect_time = None
        self.game_over_handled = False

    def get_state_json(self):


class Room:
    """חדר משחק — שני שחקנים + צופים."""

    def __init__(self, room_id, creator_ws, creator_username):
        self.room_id = room_id
        self.white_ws = creator_ws          # יוצר החדר = לבן
        self.white_user = creator_username
        self.black_ws = None
        self.black_user = None
        self.viewers = []                   # list of websockets
        self.game_session = None            # GameSession (None עד שהשחור מצטרף)

    @property
    def is_full(self):
        """שני שחקנים מחוברים."""
        return self.black_ws is not None

    def start_game(self):
        """מתחיל משחק אחרי שהשחור הצטרף."""
        game_id = self.room_id
        self.game_session = GameSession(
            game_id, self.white_ws, self.black_ws,
            self.white_user, self.black_user
        )
        active_games[game_id] = self.game_session
        return self.game_session

    def all_websockets(self):
        """כל ה-websockets בחדר (שחקנים + צופים)."""
        ws_list = []
        if self.white_ws:
            ws_list.append(self.white_ws)
        if self.black_ws:
            ws_list.append(self.black_ws)
        ws_list.extend(self.viewers)
        return ws_list
        snapshot = self.engine.get_snapshot()
        board_text = board_to_string(snapshot.board)
        return {
            "board": board_text,
            "game_over": snapshot.game_over,
            "winner": snapshot.winner,
            "white_score": snapshot.white_score,
            "black_score": snapshot.black_score,
            "timestamp": time.time() - self.start_time,
            "white_name": self.white_user,
            "black_name": self.black_user,
        }

    def get_opponent_ws(self, ws):
        if ws == self.white_ws:
            return self.black_ws
        return self.white_ws

    def get_color(self, ws):
        if ws == self.white_ws:
            return "white"
        return "black"


# --- Game ID counter ---
_game_id_counter = 0


def next_game_id():
    global _game_id_counter
    _game_id_counter += 1
    return _game_id_counter


# ===========================================================================
# Parse command
# ===========================================================================

def parse_move_command(cmd: str):
    """מפרסר פקודת move: "WRa1a5" -> (source, dest)"""
    cmd = cmd.strip()

    if cmd.startswith("JUMP"):
        parts = cmd.split()
        if len(parts) == 2:
            piece_str = parts[1]
            col = ord(piece_str[2]) - ord('a')
            row = 8 - int(piece_str[3])
            return "jump", Position(row, col)
        return None, None

    if len(cmd) == 6:
        src_col = ord(cmd[2]) - ord('a')
        src_row = 8 - int(cmd[3])
        dst_col = ord(cmd[4]) - ord('a')
        dst_row = 8 - int(cmd[5])
        return "move", (Position(src_row, src_col), Position(dst_row, dst_col))

    return None, None


# ===========================================================================
# Matchmaking
# ===========================================================================

def find_match(new_player):
    """מחפש יריב בתור עם ELO ±100."""
    for i, waiting in enumerate(matchmaking_queue):
        if abs(waiting["rating"] - new_player["rating"]) <= ELO_RANGE:
            matchmaking_queue.pop(i)
            return waiting
    return None


# ===========================================================================
# Handle client
# ===========================================================================

async def handle_client(websocket):
    """מטפל בחיבור client — login, matchmaking, game."""
    username = None
    rating = 0
    game_session = None

    try:
        async for message in websocket:
            data = json.loads(message)
            msg_type = data.get("type")

            # --- Login / Register ---
            if msg_type in ("login", "register"):
                uname = data.get("username", "")
                passwd = data.get("password", "")

                if msg_type == "register":
                    if db.register(uname, passwd):
                        print(f"[SERVER] Registered: {uname}")
                    else:
                        await websocket.send(json.dumps({
                            "type": "error", "message": "Username already exists"
                        }))
                        continue
                else:  # login
                    if not db.login(uname, passwd):
                        if not db.user_exists(uname):
                            db.register(uname, passwd)
                            print(f"[SERVER] Auto-registered: {uname}")
                        else:
                            await websocket.send(json.dumps({
                                "type": "error", "message": "Wrong password"
                            }))
                            continue

                username = uname
                rating = db.get_rating(username)
                await websocket.send(json.dumps({
                    "type": "logged_in", "username": username, "rating": rating
                }))
                print(f"[SERVER] {username} logged in (Rating: {rating})")

            # --- Play (enter matchmaking) ---
            elif msg_type == "play":
                if username is None:
                    await websocket.send(json.dumps({
                        "type": "error", "message": "Login first"
                    }))
                    continue

                new_player = {
                    "ws": websocket,
                    "username": username,
                    "rating": rating,
                    "time": time.time(),
                }

                # חיפוש יריב
                opponent = find_match(new_player)

                if opponent:
                    # מצאנו — מתחילים משחק
                    game_id = next_game_id()
                    game_session = GameSession(
                        game_id,
                        white_ws=opponent["ws"],
                        black_ws=websocket,
                        white_user=opponent["username"],
                        black_user=username,
                    )
                    active_games[game_id] = game_session

                    # שומר reference ב-opponent websocket handler
                    # שולח לשניהם
                    await opponent["ws"].send(json.dumps({
                        "type": "game_start",
                        "color": "white",
                        "opponent": username,
                        "opponent_rating": rating,
                    }))
                    await websocket.send(json.dumps({
                        "type": "game_start",
                        "color": "black",
                        "opponent": opponent["username"],
                        "opponent_rating": opponent["rating"],
                    }))

                    # שולח מצב התחלתי
                    state = game_session.get_state_json()
                    await opponent["ws"].send(json.dumps({"type": "state", "data": state}))
                    await websocket.send(json.dumps({"type": "state", "data": state}))

                    print(f"[SERVER] Game #{game_id}: {opponent['username']} (W) vs {username} (B)")
                else:
                    # לא מצאנו — נכנס לתור
                    matchmaking_queue.append(new_player)
                    await websocket.send(json.dumps({
                        "type": "searching", "message": "Looking for opponent..."
                    }))
                    print(f"[SERVER] {username} entered matchmaking queue")

            # --- Create Room ---
            elif msg_type == "create_room":
                if username is None:
                    await websocket.send(json.dumps({"type": "error", "message": "Login first"}))
                    continue

                room_id = str(uuid.uuid4())[:8]  # 8 תווים ייחודיים
                room = Room(room_id, websocket, username)
                rooms[room_id] = room
                logger.info(f"{username} created room {room_id}")

                await websocket.send(json.dumps({
                    "type": "room_created",
                    "room_id": room_id,
                    "message": f"Room created! Share this ID: {room_id}",
                }))

            # --- Join Room ---
            elif msg_type == "join_room":
                if username is None:
                    await websocket.send(json.dumps({"type": "error", "message": "Login first"}))
                    continue

                room_id = data.get("room_id", "").strip()
                if room_id not in rooms:
                    await websocket.send(json.dumps({
                        "type": "error", "message": f"Room '{room_id}' not found"
                    }))
                    continue

                room = rooms[room_id]

                if not room.is_full:
                    # שחקן שני — שחור
                    room.black_ws = websocket
                    room.black_user = username
                    logger.info(f"{username} joined room {room_id} as Black")

                    # מתחיל משחק
                    game_session = room.start_game()

                    await room.white_ws.send(json.dumps({
                        "type": "game_start",
                        "color": "white",
                        "room_id": room_id,
                        "opponent": username,
                        "opponent_rating": rating,
                    }))
                    await websocket.send(json.dumps({
                        "type": "game_start",
                        "color": "black",
                        "room_id": room_id,
                        "opponent": room.white_user,
                        "opponent_rating": db.get_rating(room.white_user),
                    }))

                    # שולח מצב לכולם (שחקנים + צופים)
                    state = game_session.get_state_json()
                    for ws in room.all_websockets():
                        try:
                            await ws.send(json.dumps({"type": "state", "data": state}))
                        except:
                            pass

                    logger.info(f"Room {room_id}: Game started! {room.white_user} vs {username}")
                else:
                    # צופה
                    room.viewers.append(websocket)
                    logger.info(f"{username} joined room {room_id} as Viewer")

                    await websocket.send(json.dumps({
                        "type": "viewer",
                        "room_id": room_id,
                        "message": "You are a viewer. Watching the game.",
                    }))

                    # שולח מצב נוכחי לצופה
                    if room.game_session:
                        state = room.game_session.get_state_json()
                        await websocket.send(json.dumps({"type": "state", "data": state}))

            # --- Game commands (move/jump) ---
            elif msg_type == "move" and game_session:
                cmd = data.get("cmd", "")
                cmd_type, cmd_data = parse_move_command(cmd)

                if cmd_type == "move":
                    source, dest = cmd_data
                    result = game_session.engine.request_move(source, dest)
                    if not result.is_accepted:
                        await websocket.send(json.dumps({
                            "type": "rejected", "reason": result.reason
                        }))
                        continue

                elif cmd_type == "jump":
                    game_session.engine.jump(cmd_data)

                # שולח state לשניהם + viewers
                state = game_session.get_state_json()
                await game_session.white_ws.send(json.dumps({"type": "state", "data": state}))
                await game_session.black_ws.send(json.dumps({"type": "state", "data": state}))
                # viewers
                room_for_game = next((r for r in rooms.values() if r.game_session == game_session), None)
                if room_for_game:
                    for v_ws in room_for_game.viewers:
                        try:
                            await v_ws.send(json.dumps({"type": "state", "data": state}))
                        except:
                            pass
                cmd = data.get("cmd", "")
                _, pos = parse_move_command(cmd)
                if pos:
                    game_session.engine.jump(pos)
                    state = game_session.get_state_json()
                    await game_session.white_ws.send(json.dumps({"type": "state", "data": state}))
                    await game_session.black_ws.send(json.dumps({"type": "state", "data": state}))

    except websockets.exceptions.ConnectionClosed:
        print(f"[SERVER] {username or 'unknown'} disconnected")

        # הסרה מtור matchmaking
        matchmaking_queue[:] = [p for p in matchmaking_queue if p["ws"] != websocket]

        # טיפול ב-disconnect באמצע משחק
        if game_session and not game_session.engine.game_over:
            color = game_session.get_color(websocket)
            game_session.disconnected_player = color
            game_session.disconnect_time = time.time()
            print(f"[SERVER] {username} disconnected mid-game. 20s countdown started.")

            # מודיע ליריב
            opponent_ws = game_session.get_opponent_ws(websocket)
            try:
                await opponent_ws.send(json.dumps({
                    "type": "opponent_disconnected",
                    "countdown": DISCONNECT_TIMEOUT,
                }))
            except:
                pass


# ===========================================================================
# Matchmaking timeout checker
# ===========================================================================

async def matchmaking_timeout_checker():
    """בודק כל שנייה אם מישהו חיכה יותר מדקה בתור."""
    while True:
        await asyncio.sleep(1)
        now = time.time()
        expired = [p for p in matchmaking_queue if now - p["time"] > MATCHMAKING_TIMEOUT]
        for player in expired:
            matchmaking_queue.remove(player)
            try:
                await player["ws"].send(json.dumps({
                    "type": "matchmaking_failed",
                    "message": "Could not find opponent. Try again later."
                }))
            except:
                pass
            print(f"[SERVER] {player['username']} matchmaking timed out")


# ===========================================================================
# Disconnect timeout checker
# ===========================================================================

async def disconnect_timeout_checker():
    """בודק כל שנייה אם שחקן מנותק עבר 20 שניות — auto-resign."""
    while True:
        await asyncio.sleep(1)
        now = time.time()

        for game_id, session in list(active_games.items()):
            if session.disconnected_player and not session.game_over_handled:
                elapsed = now - session.disconnect_time
                remaining = DISCONNECT_TIMEOUT - elapsed

                if remaining <= 0:
                    # auto-resign — המנותק מפסיד
                    winner_color = "black" if session.disconnected_player == "white" else "white"
                    winner_user = session.white_user if winner_color == "white" else session.black_user
                    loser_user = session.white_user if winner_color == "black" else session.black_user

                    session.engine.state.end_game(winner_color)
                    session.game_over_handled = True

                    # עדכון ELO
                    new_w, new_l = db.update_ratings(winner_user, loser_user)
                    print(f"[SERVER] Auto-resign: {loser_user} lost. ELO: {winner_user}={new_w}, {loser_user}={new_l}")

                    # מודיע ליריב שנשאר
                    opponent_ws = session.white_ws if winner_color == "white" else session.black_ws
                    try:
                        await opponent_ws.send(json.dumps({
                            "type": "opponent_resigned",
                            "message": f"{loser_user} disconnected. You win!",
                        }))
                    except:
                        pass

                else:
                    # שולח countdown ליריב
                    opponent_ws = session.get_opponent_ws(
                        session.white_ws if session.disconnected_player == "white" else session.black_ws
                    )
                    try:
                        await opponent_ws.send(json.dumps({
                            "type": "disconnect_countdown",
                            "seconds_remaining": int(remaining),
                        }))
                    except:
                        pass


# ===========================================================================
# Game tick — advances time for all active games
# ===========================================================================

async def game_tick():
    """מקדם זמן כל 33ms לכל המשחקים הפעילים."""
    last_time = time.time()

    while True:
        await asyncio.sleep(0.033)

        current_time = time.time()
        elapsed_ms = int((current_time - last_time) * 1000)
        last_time = current_time

        if elapsed_ms <= 0:
            continue

        for game_id, session in list(active_games.items()):
            if session.engine.game_over:
                continue

            events = session.engine.wait(elapsed_ms)
            if events:
                # שולח state מעודכן
                state = session.get_state_json()
                for ws in [session.white_ws, session.black_ws]:
                    try:
                        await ws.send(json.dumps({"type": "state", "data": state}))
                    except:
                        pass

                # בודק game over
                if session.engine.game_over and not session.game_over_handled:
                    session.game_over_handled = True
                    snapshot = session.engine.get_snapshot()
                    winner_user = session.white_user if snapshot.winner == "white" else session.black_user
                    loser_user = session.black_user if snapshot.winner == "white" else session.white_user
                    new_w, new_l = db.update_ratings(winner_user, loser_user)
                    print(f"[SERVER] Game #{game_id} over. {winner_user} wins! ELO: {new_w}/{new_l}")


# ===========================================================================
# Main
# ===========================================================================

async def main():
    print(f"[SERVER] Kung Fu Chess server running on ws://{HOST}:{PORT}")
    print("[SERVER] Waiting for players...")

    # מריץ tasks ברקע
    asyncio.create_task(game_tick())
    asyncio.create_task(matchmaking_timeout_checker())
    asyncio.create_task(disconnect_timeout_checker())

    # מריץ שרת WebSocket
    async with websockets.serve(handle_client, HOST, PORT):
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
