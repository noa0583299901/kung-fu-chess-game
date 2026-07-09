"""
שכבה: Model
Board — מחזיק את הסידור הלוגי של הכלים.
אחריות: אחסון width/height, הוספה/הסרה/שאילתה/הזזת כלי.
לא מכיל חוקי תנועה — Board יודע מה קיים, לא מה חוקי.
Board.move_piece מניח שהאימות כבר קרה.
"""
from kungfu_chess.model.position import Position
from kungfu_chess.model.piece import Piece, CAPTURED


class Board:
    def __init__(self, rows: int, cols: int):
        self.rows = rows
        self.cols = cols
        # מיפוי Position -> Piece
        self._grid = {}

    def is_inside(self, pos: Position) -> bool:
        return 0 <= pos.row < self.rows and 0 <= pos.col < self.cols

    def add_piece(self, piece: Piece):
        """מוסיף כלי ללוח. נכשל אם התא תפוס."""
        if piece.cell in self._grid:
            raise ValueError(f"Cell {piece.cell} is already occupied")
        self._grid[piece.cell] = piece

    def remove_piece(self, pos: Position):
        """מסיר כלי מהתא ומסמן אותו כ-captured."""
        piece = self._grid.pop(pos, None)
        if piece is not None:
            piece.state = CAPTURED
        return piece

    def get_piece_at(self, pos: Position):
        """מחזיר את הכלי בתא, או None אם ריק."""
        return self._grid.get(pos, None)

    def move_piece(self, source: Position, destination: Position):
        """
        מזיז כלי מ-source ל-destination.
        מניח שהאימות כבר קרה. אם יש כלי ביעד — מסיר אותו (capture).
        """
        piece = self._grid.pop(source)

        # capture אם יש כלי ביעד
        captured = self._grid.pop(destination, None)
        if captured is not None:
            captured.state = CAPTURED

        piece.cell = destination
        self._grid[destination] = piece

        return captured

    def all_pieces(self):
        """מחזיר את כל הכלים על הלוח."""
        return list(self._grid.values())
