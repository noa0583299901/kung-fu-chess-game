"""
שכבה: Movement Rules
piece_rules.py — חוקי תנועה לכל סוג כלי.

Interface: MovementStrategy.legal_destinations(board, piece) -> set[Position]
Pattern: Strategy per piece type + Registry.

כל כלי מממש MovementStrategy. הRegistry ממפה kind → strategy.
הוספת כלי חדש = כתיבת strategy חדש + רישום ב-PIECE_RULE_REGISTRY.
"""
from abc import ABC, abstractmethod

from kungfu_chess.model.position import Position
from kungfu_chess.model.piece import (
    Piece, KING, QUEEN, ROOK, BISHOP, KNIGHT, PAWN, WHITE,
)
from kungfu_chess.model.board import Board


# ===========================================================================
# MovementStrategy — Interface
# ===========================================================================

class MovementStrategy(ABC):
    """
    Interface לחוקי תנועה של כלי.
    Stateless — לא שומר state, לא עושה mutation.
    """

    @abstractmethod
    def legal_destinations(self, board: Board, piece: Piece) -> set:
        """מחזיר set[Position] של יעדים חוקיים לכלי הנתון."""
        pass


# ===========================================================================
# Helper — sliding pieces (rook, bishop, queen)
# ===========================================================================

def _sliding_destinations(board: Board, piece: Piece, directions: list) -> set:
    """עזר — מחשב יעדים לכלי חולק."""
    destinations = set()
    for dr, dc in directions:
        row = piece.cell.row + dr
        col = piece.cell.col + dc
        while True:
            pos = Position(row, col)
            if not board.is_inside(pos):
                break
            target = board.get_piece_at(pos)
            if target is None:
                destinations.add(pos)
            elif target.state == "defending":
                destinations.add(pos)
            elif target.color != piece.color:
                destinations.add(pos)
                break
            else:
                break
            row += dr
            col += dc
    return destinations


# ===========================================================================
# Strategy implementations
# ===========================================================================

class RookStrategy(MovementStrategy):
    def legal_destinations(self, board: Board, piece: Piece) -> set:
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        return _sliding_destinations(board, piece, directions)


class BishopStrategy(MovementStrategy):
    def legal_destinations(self, board: Board, piece: Piece) -> set:
        directions = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
        return _sliding_destinations(board, piece, directions)


class QueenStrategy(MovementStrategy):
    def legal_destinations(self, board: Board, piece: Piece) -> set:
        rook_dirs = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        bishop_dirs = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
        return (_sliding_destinations(board, piece, rook_dirs) |
                _sliding_destinations(board, piece, bishop_dirs))


class KnightStrategy(MovementStrategy):
    def legal_destinations(self, board: Board, piece: Piece) -> set:
        destinations = set()
        jumps = [
            (-2, -1), (-2, 1), (-1, -2), (-1, 2),
            (1, -2), (1, 2), (2, -1), (2, 1),
        ]
        for dr, dc in jumps:
            pos = Position(piece.cell.row + dr, piece.cell.col + dc)
            if not board.is_inside(pos):
                continue
            target = board.get_piece_at(pos)
            if target is None or target.color != piece.color or target.state == "defending":
                destinations.add(pos)
        return destinations


class KingStrategy(MovementStrategy):
    def legal_destinations(self, board: Board, piece: Piece) -> set:
        destinations = set()
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                pos = Position(piece.cell.row + dr, piece.cell.col + dc)
                if not board.is_inside(pos):
                    continue
                target = board.get_piece_at(pos)
                if target is None or target.color != piece.color or target.state == "defending":
                    destinations.add(pos)
        return destinations


class PawnStrategy(MovementStrategy):
    def legal_destinations(self, board: Board, piece: Piece) -> set:
        destinations = set()
        direction = -1 if piece.color == WHITE else 1
        start_row = board.rows - 2 if piece.color == WHITE else 1

        # תנועה ישרה
        forward = Position(piece.cell.row + direction, piece.cell.col)
        forward_piece = board.get_piece_at(forward)
        forward_free = forward_piece is None or forward_piece.state == "defending"
        if board.is_inside(forward) and forward_free:
            destinations.add(forward)

            # תנועה כפולה מהשורה ההתחלתית
            if piece.cell.row == start_row:
                double = Position(piece.cell.row + 2 * direction, piece.cell.col)
                double_piece = board.get_piece_at(double)
                double_free = double_piece is None or double_piece.state == "defending"
                if board.is_inside(double) and double_free:
                    destinations.add(double)

        # אכילה אלכסונית
        for dc in (-1, 1):
            diag = Position(piece.cell.row + direction, piece.cell.col + dc)
            if not board.is_inside(diag):
                continue
            target = board.get_piece_at(diag)
            if target is not None and target.color != piece.color:
                destinations.add(diag)

        return destinations


# ===========================================================================
# Registry — ממפה kind → strategy instance
# ===========================================================================

PIECE_RULE_REGISTRY = {
    ROOK: RookStrategy(),
    BISHOP: BishopStrategy(),
    QUEEN: QueenStrategy(),
    KNIGHT: KnightStrategy(),
    KING: KingStrategy(),
    PAWN: PawnStrategy(),
}


def legal_destinations(board: Board, piece: Piece) -> set:
    """נקודת כניסה ראשית — מחזירה set[Position] של יעדים חוקיים."""
    strategy = PIECE_RULE_REGISTRY.get(piece.kind)
    if strategy is None:
        return set()
    return strategy.legal_destinations(board, piece)
