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

# ---------------------------------------------------------------------------
# Piece values (for score calculation)
# ---------------------------------------------------------------------------
PIECE_VALUES = {
    "pawn": 1,
    "knight": 3,
    "bishop": 3,
    "rook": 5,
    "queen": 9,
    "king": 0,
}

# ---------------------------------------------------------------------------
# Cooldown after move (milliseconds)
# ---------------------------------------------------------------------------
COOLDOWN_DURATION_MS = 2000

# ---------------------------------------------------------------------------
# Cooldown after jump landing (milliseconds)
# ---------------------------------------------------------------------------
JUMP_COOLDOWN_MS = 1000

# ---------------------------------------------------------------------------
# Rendering layout constants
# ---------------------------------------------------------------------------
RENDER_CELL_SIZE = 70       # pixels per cell in GUI rendering
SIDE_PANEL_WIDTH = 160      # pixels — moves log panels width
TOP_BAR_HEIGHT = 30         # pixels — player name bar height
BOTTOM_BAR_HEIGHT = 60      # pixels — score bar height
