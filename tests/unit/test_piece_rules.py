"""
Unit tests for PieceRules (iterations 3 + 7).
Tests legal_destinations for each piece type: rook, bishop, queen, knight, king, pawn.
"""
import pytest
from kungfu_chess.model.position import Position
from kungfu_chess.model.piece import (
    Piece, WHITE, BLACK,
    ROOK, BISHOP, QUEEN, KNIGHT, KING, PAWN,
)
from kungfu_chess.model.board import Board
from kungfu_chess.rules.piece_rules import legal_destinations


# ===========================================================================
# Rook (iteration 3)
# ===========================================================================

class TestRookDestinations:

    def test_rook_on_empty_board_covers_row_and_column(self):
        board = Board(8, 8)
        rook = Piece(1, WHITE, ROOK, Position(3, 3))
        board.add_piece(rook)
        dests = legal_destinations(board, rook)
        # 7 in row + 7 in col = 14
        assert len(dests) == 14

    def test_rook_blocked_by_friendly_piece(self):
        board = Board(8, 8)
        rook = Piece(1, WHITE, ROOK, Position(0, 0))
        friendly = Piece(2, WHITE, PAWN, Position(0, 3))
        board.add_piece(rook)
        board.add_piece(friendly)
        dests = legal_destinations(board, rook)
        # Cannot reach (0,3) or beyond in that direction
        assert Position(0, 3) not in dests
        assert Position(0, 4) not in dests
        # Can reach (0,1) and (0,2)
        assert Position(0, 1) in dests
        assert Position(0, 2) in dests

    def test_rook_includes_enemy_blocker_as_destination(self):
        board = Board(8, 8)
        rook = Piece(1, WHITE, ROOK, Position(0, 0))
        enemy = Piece(2, BLACK, PAWN, Position(0, 3))
        board.add_piece(rook)
        board.add_piece(enemy)
        dests = legal_destinations(board, rook)
        # Can reach enemy at (0,3) — capture
        assert Position(0, 3) in dests
        # Cannot pass enemy
        assert Position(0, 4) not in dests

    def test_rook_cannot_move_diagonally(self):
        board = Board(8, 8)
        rook = Piece(1, WHITE, ROOK, Position(3, 3))
        board.add_piece(rook)
        dests = legal_destinations(board, rook)
        assert Position(4, 4) not in dests
        assert Position(2, 2) not in dests


# ===========================================================================
# Bishop (iteration 7)
# ===========================================================================

class TestBishopDestinations:

    def test_bishop_moves_diagonally(self):
        board = Board(8, 8)
        bishop = Piece(1, WHITE, BISHOP, Position(3, 3))
        board.add_piece(bishop)
        dests = legal_destinations(board, bishop)
        assert Position(4, 4) in dests
        assert Position(5, 5) in dests
        assert Position(2, 2) in dests
        assert Position(4, 2) in dests

    def test_bishop_cannot_move_straight(self):
        board = Board(8, 8)
        bishop = Piece(1, WHITE, BISHOP, Position(3, 3))
        board.add_piece(bishop)
        dests = legal_destinations(board, bishop)
        assert Position(3, 5) not in dests
        assert Position(5, 3) not in dests

    def test_bishop_blocked_by_friendly(self):
        board = Board(8, 8)
        bishop = Piece(1, WHITE, BISHOP, Position(0, 0))
        friendly = Piece(2, WHITE, PAWN, Position(2, 2))
        board.add_piece(bishop)
        board.add_piece(friendly)
        dests = legal_destinations(board, bishop)
        assert Position(1, 1) in dests
        assert Position(2, 2) not in dests
        assert Position(3, 3) not in dests


# ===========================================================================
# Queen (iteration 7)
# ===========================================================================

class TestQueenDestinations:

    def test_queen_combines_rook_and_bishop(self):
        board = Board(8, 8)
        queen = Piece(1, WHITE, QUEEN, Position(3, 3))
        board.add_piece(queen)
        dests = legal_destinations(board, queen)
        # Rook-like
        assert Position(3, 7) in dests
        assert Position(0, 3) in dests
        # Bishop-like
        assert Position(5, 5) in dests
        assert Position(1, 1) in dests


# ===========================================================================
# Knight (iteration 7)
# ===========================================================================

class TestKnightDestinations:

    def test_knight_L_shape_moves(self):
        board = Board(8, 8)
        knight = Piece(1, WHITE, KNIGHT, Position(4, 4))
        board.add_piece(knight)
        dests = legal_destinations(board, knight)
        expected = {
            Position(2, 3), Position(2, 5),
            Position(3, 2), Position(3, 6),
            Position(5, 2), Position(5, 6),
            Position(6, 3), Position(6, 5),
        }
        assert dests == expected

    def test_knight_jumps_over_blockers(self):
        board = Board(8, 8)
        knight = Piece(1, WHITE, KNIGHT, Position(0, 0))
        # Surround with friendly pieces
        board.add_piece(knight)
        board.add_piece(Piece(2, WHITE, PAWN, Position(0, 1)))
        board.add_piece(Piece(3, WHITE, PAWN, Position(1, 0)))
        board.add_piece(Piece(4, WHITE, PAWN, Position(1, 1)))
        dests = legal_destinations(board, knight)
        # Knight can still jump to (2,1) and (1,2)
        assert Position(2, 1) in dests
        assert Position(1, 2) in dests

    def test_knight_cannot_land_on_friendly(self):
        board = Board(8, 8)
        knight = Piece(1, WHITE, KNIGHT, Position(0, 0))
        friendly = Piece(2, WHITE, PAWN, Position(2, 1))
        board.add_piece(knight)
        board.add_piece(friendly)
        dests = legal_destinations(board, knight)
        assert Position(2, 1) not in dests
        assert Position(1, 2) in dests


# ===========================================================================
# King (iteration 7)
# ===========================================================================

class TestKingDestinations:

    def test_king_moves_one_cell_in_any_direction(self):
        board = Board(8, 8)
        king = Piece(1, WHITE, KING, Position(4, 4))
        board.add_piece(king)
        dests = legal_destinations(board, king)
        assert len(dests) == 8
        assert Position(3, 3) in dests
        assert Position(4, 5) in dests
        assert Position(5, 4) in dests

    def test_king_cannot_move_two_cells(self):
        board = Board(8, 8)
        king = Piece(1, WHITE, KING, Position(4, 4))
        board.add_piece(king)
        dests = legal_destinations(board, king)
        assert Position(4, 6) not in dests
        assert Position(6, 4) not in dests

    def test_king_at_corner(self):
        board = Board(8, 8)
        king = Piece(1, WHITE, KING, Position(0, 0))
        board.add_piece(king)
        dests = legal_destinations(board, king)
        assert len(dests) == 3


# ===========================================================================
# Pawn (iteration 7)
# ===========================================================================

class TestPawnDestinations:

    def test_white_pawn_moves_one_row_up(self):
        board = Board(8, 8)
        pawn = Piece(1, WHITE, PAWN, Position(4, 3))
        board.add_piece(pawn)
        dests = legal_destinations(board, pawn)
        assert Position(3, 3) in dests

    def test_black_pawn_moves_one_row_down(self):
        board = Board(8, 8)
        pawn = Piece(1, BLACK, PAWN, Position(3, 3))
        board.add_piece(pawn)
        dests = legal_destinations(board, pawn)
        assert Position(4, 3) in dests

    def test_pawn_blocked_by_piece_ahead(self):
        board = Board(8, 8)
        pawn = Piece(1, WHITE, PAWN, Position(4, 3))
        blocker = Piece(2, BLACK, PAWN, Position(3, 3))
        board.add_piece(pawn)
        board.add_piece(blocker)
        dests = legal_destinations(board, pawn)
        assert Position(3, 3) not in dests

    def test_pawn_captures_diagonally(self):
        board = Board(8, 8)
        pawn = Piece(1, WHITE, PAWN, Position(4, 3))
        enemy = Piece(2, BLACK, PAWN, Position(3, 4))
        board.add_piece(pawn)
        board.add_piece(enemy)
        dests = legal_destinations(board, pawn)
        assert Position(3, 4) in dests

    def test_pawn_cannot_capture_empty_diagonal(self):
        board = Board(8, 8)
        pawn = Piece(1, WHITE, PAWN, Position(4, 3))
        board.add_piece(pawn)
        dests = legal_destinations(board, pawn)
        assert Position(3, 4) not in dests
        assert Position(3, 2) not in dests

    def test_pawn_double_move_from_start_row(self):
        """Pawn can move 2 from start row (rows-2 for white, 1 for black)."""
        board = Board(8, 8)
        pawn = Piece(1, WHITE, PAWN, Position(6, 3))
        board.add_piece(pawn)
        dests = legal_destinations(board, pawn)
        assert Position(4, 3) in dests
        assert Position(5, 3) in dests
