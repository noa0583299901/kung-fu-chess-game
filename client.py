"""
Kung Fu Chess — WebSocket Client

Flow:
    1. Login/Register
    2. Press Play → matchmaking
    3. Game starts → send moves, receive state
"""
import asyncio
import json
import websockets
import sys

SERVER_URL = "ws://localhost:8765"


async def receive_messages(websocket):
    """מקבל הודעות מה-Server ומציג אותן."""
    try:
        async for message in websocket:
            data = json.loads(message)
            msg_type = data.get("type")

            if msg_type == "logged_in":
                print(f"\n✓ Logged in as: {data['username']} (Rating: {data['rating']})")
                print("\nType 'play' to find a game, 'quit' to exit")
                print("> ", end="", flush=True)

            elif msg_type == "searching":
                print(f"\n⏳ {data['message']}")
                print("   (waiting up to 60 seconds...)")

            elif msg_type == "matchmaking_failed":
                print(f"\n✗ {data['message']}")
                print("> ", end="", flush=True)

            elif msg_type == "game_start":
                color = data["color"]
                opponent = data["opponent"]
                opp_rating = data["opponent_rating"]
                print(f"\n{'='*40}")
                print(f"  GAME FOUND!")
                print(f"  You are: {color.upper()}")
                print(f"  Opponent: {opponent} (Rating: {opp_rating})")
                print(f"{'='*40}")
                print("\nCommands: WRa1a5 (move), JUMP WPe2 (jump), quit")
                print("> ", end="", flush=True)

            elif msg_type == "state":
                state = data["data"]
                print(f"\n{'='*40}")
                print(state["board"])
                print(f"Score: White={state['white_score']} | Black={state['black_score']}")
                if state.get("game_over"):
                    winner = state.get("winner", "?")
                    print(f"\n*** GAME OVER — {winner} wins! ***")
                print(f"{'='*40}")
                print("> ", end="", flush=True)

            elif msg_type == "rejected":
                print(f"  [Rejected: {data['reason']}]")
                print("> ", end="", flush=True)

            elif msg_type == "error":
                print(f"  [Error: {data['message']}]")
                print("> ", end="", flush=True)

            elif msg_type == "opponent_disconnected":
                countdown = data["countdown"]
                print(f"\n⚠ Opponent disconnected! Auto-resign in {countdown}s...")

            elif msg_type == "disconnect_countdown":
                remaining = data["seconds_remaining"]
                print(f"  ⏱ Opponent returns in {remaining}s...", end="\r", flush=True)

            elif msg_type == "opponent_resigned":
                print(f"\n🏆 {data['message']}")
                print("> ", end="", flush=True)

    except websockets.exceptions.ConnectionClosed:
        print("\n[Disconnected from server]")


async def send_commands(websocket):
    """קורא פקודות מהמשתמש ושולח לServer."""
    loop = asyncio.get_event_loop()

    while True:
        cmd = await loop.run_in_executor(None, sys.stdin.readline)
        cmd = cmd.strip()

        if cmd.lower() == "quit":
            await websocket.close()
            break

        if cmd.lower() == "play":
            await websocket.send(json.dumps({"type": "play"}))

        elif cmd.startswith("JUMP"):
            await websocket.send(json.dumps({"type": "jump", "cmd": cmd}))

        elif len(cmd) == 6 and cmd[0] in "WB":
            await websocket.send(json.dumps({"type": "move", "cmd": cmd}))

        elif cmd:
            print("  Unknown command. Use: WRa1a5 / JUMP WPe2 / play / quit")
            print("> ", end="", flush=True)


async def main():
    # --- Home screen ---
    print("=" * 40)
    print("   KUNG FU CHESS")
    print("=" * 40)
    print("\n1. Login")
    print("2. Register")
    choice = input("\nChoice (1/2): ").strip()

    username = input("Username: ").strip()
    password = input("Password: ").strip()

    if not username or not password:
        print("Username and password required!")
        return

    action = "register" if choice == "2" else "login"

    print(f"\nConnecting to server...")

    async with websockets.connect(SERVER_URL) as websocket:
        # שולח login/register
        await websocket.send(json.dumps({
            "type": action,
            "username": username,
            "password": password,
        }))

        # מריץ קבלה ושליחה במקביל
        receive_task = asyncio.create_task(receive_messages(websocket))
        send_task = asyncio.create_task(send_commands(websocket))

        done, pending = await asyncio.wait(
            [receive_task, send_task],
            return_when=asyncio.FIRST_COMPLETED
        )

        for task in pending:
            task.cancel()


if __name__ == "__main__":
    asyncio.run(main())
