from game.board import is_inside_board, pixel_to_cell, print_board, move_piece, is_king
from game.constants import EMPTY_CELL
from game.pieces import same_color
from game.rules import is_legal_move, is_path_clear
from game.timing import PendingMove, move_duration

CMD_CLICK = "click"
CMD_WAIT = "wait"
CMD_PRINT = "print"
PRINT_BOARD_ARG = "board"


def handle_click(parts, board, selected, pending):
    """
    מטפל בפקודת click.
    מחזיר (selected, pending) מעודכנים.
    """
    # בזמן שכלי נע מתעלמים מכל לחיצה
    if pending is not None:
        return selected, pending

    x = int(parts[1])
    y = int(parts[2])

    if x < 0 or y < 0:
        return selected, pending

    rows = len(board)
    cols = len(board[0])
    row, col = pixel_to_cell(x, y)

    if not is_inside_board(row, col, rows, cols):
        return selected, pending

    cell = board[row][col]

    if selected is None:
        if cell != EMPTY_CELL:
            selected = (row, col)
        return selected, pending

    source_row, source_col = selected
    piece = board[source_row][source_col]

    # בחירת כלי אחר מאותו צבע
    if same_color(cell, piece):
        return (row, col), pending

    # חוקיות התנועה
    if not is_legal_move(board, piece, source_row, source_col, row, col):
        return None, pending

    # חסימות
    if not is_path_clear(board, piece, source_row, source_col, row, col):
        return None, pending

    duration = move_duration(piece, source_row, source_col, row, col)
    pending = PendingMove(
        source_row=source_row,
        source_col=source_col,
        target_row=row,
        target_col=col,
        duration=duration,
    )
    return None, pending


def handle_wait(parts, board, pending):
    """
    מטפל בפקודת wait.
    מחזיר (pending, game_over).
    game_over=True אם המהלך הסתיים ונאכל מלך.
    """
    if pending is None:
        return None, False

    milliseconds = int(parts[1])
    pending.elapsed += milliseconds

    if pending.elapsed >= pending.duration:
        target = board[pending.target_row][pending.target_col]
        game_over = is_king(target)
        move_piece(board, pending.source_row, pending.source_col,
                   pending.target_row, pending.target_col)
        return None, game_over

    return pending, False


def process_commands(command_lines, board):
    """
    מעבד את כל שורות הפקודות ומפעיל את הטיפולים המתאימים.
    אחרי game-over, click ו-wait מתעלמים — אבל print עדיין עובד.
    """
    selected = None
    pending = None
    game_over = False

    for line in command_lines:
        parts = line.split()
        if not parts:
            continue

        command = parts[0]

        if command == CMD_CLICK:
            if not game_over:
                selected, pending = handle_click(parts, board, selected, pending)

        elif command == CMD_WAIT:
            if not game_over:
                pending, game_over = handle_wait(parts, board, pending)

        elif command == CMD_PRINT:
            if len(parts) == 2 and parts[1] == PRINT_BOARD_ARG:
                print_board(board)
