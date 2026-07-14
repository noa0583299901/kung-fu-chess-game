"""
שכבה: TextTestRunner
script_runner.py — Command-script test harness.
מריץ פקודות DSL דרך ה-public command path (Controller + GameEngine).
תלוי ב-BoardParser, BoardPrinter, Controller, GameEngine.
לא מכיל: חוקי תנועה, Board mutation ישיר, או לוגיקת משחק מכפילה.
Pattern: Command-script test harness.
"""
from kungfu_chess.io.board_parser import parse_board
from kungfu_chess.io.board_printer import print_board
from kungfu_chess.engine.game_engine import GameEngine
from kungfu_chess.input.controller import Controller
from kungfu_chess.input.board_mapper import pixel_to_position
from kungfu_chess.texttests.script_parser import parse_script
from kungfu_chess.constants import CMD_CLICK, CMD_JUMP, CMD_WAIT, CMD_PRINT, PRINT_BOARD_ARG


def run_script(lines: list):
    """
    מריץ script שלם: מפרסר, בונה board, ומריץ commands.
    """
    board_lines, command_lines = parse_script(lines)
    if board_lines is None:
        return

    board, error = parse_board(board_lines)
    if error is not None:
        print(error)
        return
    if board is None:
        return

    engine = GameEngine(board)
    controller = Controller(engine)

    run_commands(command_lines, engine, controller)


def run_commands(command_lines: list, engine: GameEngine, controller: Controller):
    """
    מריץ רשימת פקודות DSL.
    """
    for line in command_lines:
        parts = line.split()
        if not parts:
            continue

        command = parts[0]

        if command == CMD_CLICK:
            x = int(parts[1])
            y = int(parts[2])
            controller.handle_click(x, y)

        elif command == CMD_JUMP:
            x = int(parts[1])
            y = int(parts[2])
            pos = pixel_to_position(x, y)
            engine.jump(pos)

        elif command == CMD_WAIT:
            milliseconds = int(parts[1])
            engine.wait(milliseconds)

        elif command == CMD_PRINT:
            if len(parts) == 2 and parts[1] == PRINT_BOARD_ARG:
                print_board(engine.get_snapshot().board)
