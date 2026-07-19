"""
Kung Fu Chess — WebSocket Client

מתחבר לServer, מקבל מצב לוח, שולח פקודות.

שימוש:
    python client.py

פקודות:
    הקלד מהלך כמו: WRa1a5 (White Rook from a1 to a5)
    או: JUMP WPe2 (White Pawn at e2 jumps)
    או: quit (יציאה)
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

            if msg_type == "assigned":
                color = data["color"]
                print(f"\n--- You are: {color.upper()} ---\n")

            elif msg_type == "state":
                state = data["data"]
                print("\n" + "=" * 40)
                print(state["board"])
                print(f"Score: White={state['white_score']} | Black={state['black_score']}")
                if state["game_over"]:
                    print(f"*** GAME OVER — {state['winner']} wins! ***")
                print("=" * 40)
                print("Your move: ", end="", flush=True)

            elif msg_type == "rejected":
                print(f"  [Rejected: {data['reason']}]")
                print("Your move: ", end="", flush=True)

            elif msg_type == "error":
                print(f"  [Error: {data['message']}]")

    except websockets.exceptions.ConnectionClosed:
        print("\n[Disconnected from server]")


async def send_commands(websocket):
    """קורא פקודות מהמשתמש ושולח לServer."""
    loop = asyncio.get_event_loop()

    while True:
        # קורא input בצורה שלא חוסמת
        cmd = await loop.run_in_executor(None, sys.stdin.readline)
        cmd = cmd.strip()

        if cmd.lower() == "quit":
            await websocket.close()
            break

        if cmd:
            await websocket.send(cmd)


async def main():
    # --- Home screen: Login ---
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

    print(f"\nConnecting to {SERVER_URL}...")

    async with websockets.connect(SERVER_URL) as websocket:
        # שולח login/register
        await websocket.send(json.dumps({
            "type": action,
            "username": username,
            "password": password,
        }))

        # מחכה לתשובה
        response = await websocket.recv()
        data = json.loads(response)

        if data.get("type") == "error":
            print(f"Error: {data['message']}")
            return

        if data.get("type") == "assigned":
            color = data["color"]
            rating = data.get("rating", 1200)
            print(f"\nWelcome {username}! (Rating: {rating})")
            print(f"You are: {color.upper()}")
            print("Waiting for opponent...")

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
