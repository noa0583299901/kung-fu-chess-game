"""
שכבה: TextTestRunner
script_parser.py — מפרסר את ה-DSL הטקסטואלי.
מפריד בין שורות Board לבין Commands.
לא מריץ כלום — רק מפרסר.

Supports both "Board:" with "Commands:" separator,
and "Board" without explicit "Commands:" (commands start after board rows).
"""

BOARD_HEADERS = ("Board:", "Board")
COMMANDS_HEADER = "Commands:"


def parse_script(lines: list) -> tuple:
    """
    מפרסר שורות DSL.
    מחזיר (board_lines, command_lines) או (None, None) אם חסר header.
    """
    # מסנן שורות ריקות
    lines = [line for line in lines if line.strip()]

    # מוצא את header הלוח
    board_idx = None
    for i, line in enumerate(lines):
        if line.strip() in BOARD_HEADERS:
            board_idx = i
            break

    if board_idx is None:
        return None, None

    # מוצא את Commands: אם קיים
    commands_idx = None
    for i, line in enumerate(lines):
        if line.strip() == COMMANDS_HEADER:
            commands_idx = i
            break

    if commands_idx is not None:
        # פורמט עם Commands: header
        board_lines = lines[board_idx + 1:commands_idx]
        command_lines = lines[commands_idx + 1:]
    else:
        # פורמט בלי Commands: — שורות הלוח עד שמגיעים לפקודה (click/wait/print)
        board_lines = []
        command_start = None
        command_keywords = ("click", "wait", "print")
        for i in range(board_idx + 1, len(lines)):
            if lines[i].split()[0] in command_keywords:
                command_start = i
                break
            board_lines.append(lines[i])

        if command_start is None:
            command_lines = []
        else:
            command_lines = lines[command_start:]

    return board_lines, command_lines
