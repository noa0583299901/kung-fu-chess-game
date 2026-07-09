"""
שכבה: TextTestRunner
script_parser.py — מפרסר את ה-DSL הטקסטואלי.
מפריד בין שורות Board לבין Commands.
לא מריץ כלום — רק מפרסר.
"""

BOARD_HEADER = "Board:"
COMMANDS_HEADER = "Commands:"


def parse_script(lines: list) -> tuple:
    """
    מפרסר שורות DSL.
    מחזיר (board_lines, command_lines) או (None, None) אם חסר header.
    """
    # מסנן שורות ריקות
    lines = [line for line in lines if line.strip()]

    if BOARD_HEADER not in lines or COMMANDS_HEADER not in lines:
        return None, None

    board_start = lines.index(BOARD_HEADER) + 1
    commands_start = lines.index(COMMANDS_HEADER)

    board_lines = lines[board_start:commands_start]
    command_lines = lines[commands_start + 1:]

    return board_lines, command_lines
