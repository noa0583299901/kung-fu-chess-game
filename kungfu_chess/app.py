"""
Entry point — קורא stdin ומריץ את ה-script.
"""
from kungfu_chess.texttests.script_runner import run_script


def main():
    lines = []
    while True:
        try:
            lines.append(input().strip())
        except EOFError:
            break
    run_script(lines)


if __name__ == "__main__":
    main()
