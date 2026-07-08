from game.constants import EMPTY_CELL


def get_color(piece):
    return piece[0]


def get_type(piece):
    return piece[1]


def same_color(piece1, piece2):
    if piece1 == EMPTY_CELL or piece2 == EMPTY_CELL:
        return False
    return get_color(piece1) == get_color(piece2)
