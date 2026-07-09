"""
שכבה: Model
Position — value object שמייצג תא בלוח.
לא יודע על גודל הלוח, פיקסלים, חוקי תנועה, או rendering.
"""


class Position:
    def __init__(self, row: int, col: int):
        self.row = row
        self.col = col

    def __eq__(self, other):
        if not isinstance(other, Position):
            return False
        return self.row == other.row and self.col == other.col

    def __hash__(self):
        return hash((self.row, self.col))

    def __repr__(self):
        return f"Position(row={self.row}, col={self.col})"
