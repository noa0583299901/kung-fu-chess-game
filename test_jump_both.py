from kungfu_chess.texttests.script_runner import run_script
import io, sys

def capture(lines):
    old = sys.stdout
    sys.stdout = buf = io.StringIO()
    run_script(lines)
    sys.stdout = old
    return buf.getvalue().strip()

def test(name, lines, expected):
    actual = capture(lines)
    status = "PASS" if actual == expected else "FAIL"
    print(f"  {status}: {name}")
    if status == "FAIL":
        print(f"    expected: {repr(expected)}")
        print(f"    actual:   {repr(actual)}")

# Test 47: airborne piece captures arriving enemy (jump still active)
test("airborne_captures_arriving", [
    "Board:", ". . .", "wK bR .", ". . .", "Commands:",
    "jump 50 150", "click 150 150", "click 50 150", "wait 1000", "print board"
], ". . .\nwK . .\n. . .")

# Test 49: enemy arrives AFTER landing — normal capture
test("enemy_arrives_after_landing", [
    "Board:", ". . . .", "wK . . bR", ". . . .", "Commands:",
    "jump 50 150", "wait 1000",
    "click 350 150", "click 50 150", "wait 3000", "print board"
], ". . . .\nbR . . .\n. . . .")
