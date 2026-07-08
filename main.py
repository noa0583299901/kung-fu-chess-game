# Git repo URL: <YOUR_REPO_URL_HERE>

from game.parser import parse_input
from game.board import validate_board
from game.commands import process_commands


def main():
    lines = []
    while True:
        try:
            lines.append(input().strip())
        except EOFError:
            break

    board, command_lines = parse_input(lines)
    if board is None:
        return

    valid, error = validate_board(board)
    if not valid:
        if error:
            print(error)
        return

    process_commands(command_lines, board)


main()
