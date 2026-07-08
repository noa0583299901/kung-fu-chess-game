from game.constants import BOARD_HEADER, COMMANDS_HEADER


def parse_input(lines):
    """
    מפרסר את שורות הקלט.
    מחזיר (board, command_lines) או (None, None) אם הקלט לא תקין.
    """
    lines = [line for line in lines if line]

    if BOARD_HEADER not in lines or COMMANDS_HEADER not in lines:
        return None, None

    board_start = lines.index(BOARD_HEADER) + 1
    commands_start = lines.index(COMMANDS_HEADER)

    board_lines = lines[board_start:commands_start]
    board = [line.split() for line in board_lines]

    command_lines = lines[commands_start + 1:]

    return board, command_lines
