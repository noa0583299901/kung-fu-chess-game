"""
קבועים מרכזיים של הפרויקט.
כל ה-strings וה-magic values מרוכזים כאן.
"""

# ---------------------------------------------------------------------------
# MoveResult reasons (GameEngine level)
# ---------------------------------------------------------------------------
REASON_OK = "ok"
REASON_GAME_OVER = "game_over"
REASON_MOTION_IN_PROGRESS = "motion_in_progress"

# ---------------------------------------------------------------------------
# MoveValidation reasons (RuleEngine level)
# ---------------------------------------------------------------------------
REASON_OUTSIDE_BOARD = "outside_board"
REASON_EMPTY_SOURCE = "empty_source"
REASON_FRIENDLY_DESTINATION = "friendly_destination"
REASON_ILLEGAL_PIECE_MOVE = "illegal_piece_move"

# ---------------------------------------------------------------------------
# Board parsing errors
# ---------------------------------------------------------------------------
ERROR_ROW_WIDTH = "ERROR ROW_WIDTH_MISMATCH"
ERROR_UNKNOWN_TOKEN = "ERROR UNKNOWN_TOKEN"

# ---------------------------------------------------------------------------
# DSL command names
# ---------------------------------------------------------------------------
CMD_CLICK = "click"
CMD_JUMP = "jump"
CMD_WAIT = "wait"
CMD_PRINT = "print"
PRINT_BOARD_ARG = "board"

# ---------------------------------------------------------------------------
# Board text representation
# ---------------------------------------------------------------------------
EMPTY_CELL = "."
