"""
שכבה: Movement Rules
piece_rules.py — חוקי תנועה לכל סוג כלי.
Interface: legal_destinations(board, piece) -> set[Position]
מחזיר את כל היעדים החוקיים — כולל תאים תפוסים באויב (capture).
עוצר לפני כלי ידידותי (blocking).
לא מבצע: capture, remove, move, או כל mutation.
Stateless — לא שומר selected, motions, elapsed, או game-over.
Pattern: Strategy per piece type.
"""
from kungfu_chess.model.position import Position
from kungfu_chess.model.piece import (
    Piece, KING, QUEEN, ROOK, BISHOP, KNIGHT, PAWN, WHITE,
)
from kungfu_chess.model.board import Board


def _sliding_destinations(board: Board, piece: Piece, directions: list) -> set:
    """עזר — מחשב יעדים לכלי חולק (rook, bishop, queen)."""
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
            elif target.color != piece.color:
                destinations.add(pos)  # capture — אבל עוצרים אחריו
                break
            else:
                break  # friendly blocker — עוצרים לפניו
            row += dr
            col += dc
    return destinations


def rook_destinations(board: Board, piece: Piece) -> set:
    directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
    return _sliding_destinations(board, piece, directions)


def bishop_destinations(board: Board, piece: Piece) -> set:
    directions = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
    return _sliding_destinations(board, piece, directions)


def queen_destinations(board: Board, piece: Piece) -> set:
    return rook_destinations(board, piece) | bishop_destinations(board, piece)


def knight_destinations(board: Board, piece: Piece) -> set:
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
        if target is None or target.color != piece.color:
            destinations.add(pos)
    return destinations


def king_destinations(board: Board, piece: Piece) -> set:
    destinations = set()
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue
            pos = Position(piece.cell.row + dr, piece.cell.col + dc)
            if not board.is_inside(pos):
                continue
            target = board.get_piece_at(pos)
            if target is None or target.color != piece.color:
                destinations.add(pos)
    return destinations


def pawn_destinations(board: Board, piece: Piece) -> set:
    """
    פאון:
    - לבן עולה שורה אחת, שחור יורד שורה אחת
    - תנועה כפולה מהשורה ההתחלתית (rows-1 ללבן, 0 לשחור)
    - אכילה אלכסונית צעד אחד קדימה
    - אין en passant
    """
    destinations = set()
    direction = -1 if piece.color == WHITE else 1
    start_row = board.rows - 2 if piece.color == WHITE else 1

    # תנועה ישרה — צעד אחד
    forward = Position(piece.cell.row + direction, piece.cell.col)
    if board.is_inside(forward) and board.get_piece_at(forward) is None:
        destinations.add(forward)

        # תנועה כפולה — רק מהשורה ההתחלתית ואם הצעד הראשון פנוי
        if piece.cell.row == start_row:
            double = Position(piece.cell.row + 2 * direction, piece.cell.col)
            if board.is_inside(double) and board.get_piece_at(double) is None:
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


# מילון מיפוי: סוג כלי → פונקציית יעדים (Strategy pattern)
PIECE_DESTINATIONS = {
    ROOK: rook_destinations,
    BISHOP: bishop_destinations,
    QUEEN: queen_destinations,
    KNIGHT: knight_destinations,
    KING: king_destinations,
    PAWN: pawn_destinations,
}


def legal_destinations(board: Board, piece: Piece) -> set:
    """נקודת כניסה ראשית — מחזירה set[Position] של יעדים חוקיים."""
    rule_fn = PIECE_DESTINATIONS.get(piece.kind)
    if rule_fn is None:
        return set()
    return rule_fn(board, piece)
