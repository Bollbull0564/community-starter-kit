"""Board logic for Kung Fu Xiangqi."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple

from .pieces import Color, Piece, PieceType, Position

BOARD_WIDTH = 9
BOARD_HEIGHT = 10
PALACE_FILES = range(3, 6)
RED_PALACE_RANKS = range(0, 3)
BLACK_PALACE_RANKS = range(7, 10)
RIVER_RANK = 4


@dataclass
class Move:
    piece: Piece
    start: Position
    end: Position
    captured: Optional[Piece]


class IllegalMove(Exception):
    """Raised when a move violates the rules of Xiangqi."""


class Board:
    """Represents the Xiangqi board and enforces movement rules."""

    def __init__(self, setup: bool = True) -> None:
        self._grid: Dict[Position, Piece] = {}
        if setup:
            self.setup_initial_positions()

    # ------------------------------------------------------------------
    # Board basics
    # ------------------------------------------------------------------
    def clone(self) -> "Board":
        new_board = Board(setup=False)
        for position, piece in self._grid.items():
            new_board._grid[position] = piece.copy()
        return new_board

    def setup_initial_positions(self) -> None:
        """Place all pieces in their standard starting locations."""
        self._grid.clear()
        # Red side
        self._place_home_row(Color.RED, 0)
        self._place_soldiers(Color.RED, 3)
        self._place_cannons(Color.RED, 2)
        # Black side
        self._place_home_row(Color.BLACK, BOARD_HEIGHT - 1)
        self._place_soldiers(Color.BLACK, BOARD_HEIGHT - 4)
        self._place_cannons(Color.BLACK, BOARD_HEIGHT - 3)

    def _place_home_row(self, color: Color, rank: int) -> None:
        order = [
            PieceType.CHARIOT,
            PieceType.HORSE,
            PieceType.ELEPHANT,
            PieceType.ADVISOR,
            PieceType.GENERAL,
            PieceType.ADVISOR,
            PieceType.ELEPHANT,
            PieceType.HORSE,
            PieceType.CHARIOT,
        ]
        for file, piece_type in enumerate(order):
            position = (file, rank)
            self._grid[position] = Piece(color=color, piece_type=piece_type, position=position)

    def _place_soldiers(self, color: Color, rank: int) -> None:
        for file in range(0, BOARD_WIDTH, 2):
            position = (file, rank)
            self._grid[position] = Piece(color=color, piece_type=PieceType.SOLDIER, position=position)

    def _place_cannons(self, color: Color, rank: int) -> None:
        for file in (1, BOARD_WIDTH - 2):
            position = (file, rank)
            self._grid[position] = Piece(color=color, piece_type=PieceType.CANNON, position=position)

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------
    def in_bounds(self, position: Position) -> bool:
        file, rank = position
        return 0 <= file < BOARD_WIDTH and 0 <= rank < BOARD_HEIGHT

    def get_piece(self, position: Position) -> Optional[Piece]:
        return self._grid.get(position)

    def pieces(self) -> Iterable[Piece]:
        return self._grid.values()

    def general_position(self, color: Color) -> Optional[Position]:
        for piece in self._grid.values():
            if piece.color == color and piece.piece_type == PieceType.GENERAL:
                return piece.position
        return None

    # ------------------------------------------------------------------
    # Move application
    # ------------------------------------------------------------------
    def move_piece(self, start: Position, end: Position) -> Move:
        if start not in self._grid:
            raise IllegalMove("No piece at start position")
        piece = self._grid[start]
        captured = self._grid.get(end)
        piece = piece.copy()
        del self._grid[start]
        if captured:
            del self._grid[end]
        piece.position = end
        self._grid[end] = piece
        return Move(piece=piece, start=start, end=end, captured=captured)

    # ------------------------------------------------------------------
    # Rules enforcement
    # ------------------------------------------------------------------
    def validate_move(self, piece: Piece, destination: Position) -> None:
        if not self.in_bounds(destination):
            raise IllegalMove("Destination is out of bounds")

        target = self.get_piece(destination)
        if target and target.color == piece.color:
            raise IllegalMove("Cannot capture your own piece")

        rule_validator = {
            PieceType.GENERAL: self._validate_general,
            PieceType.ADVISOR: self._validate_advisor,
            PieceType.ELEPHANT: self._validate_elephant,
            PieceType.HORSE: self._validate_horse,
            PieceType.CHARIOT: self._validate_chariot,
            PieceType.CANNON: self._validate_cannon,
            PieceType.SOLDIER: self._validate_soldier,
        }[piece.piece_type]

        rule_validator(piece, destination)
        self._validate_general_face_rule(piece, destination)
        self._validate_no_self_check(piece, destination)

    def _validate_general(self, piece: Piece, destination: Position) -> None:
        if not self._in_palace(destination, piece.color):
            raise IllegalMove("General must stay within the palace")
        start_file, start_rank = piece.position
        file, rank = destination
        if abs(start_file - file) + abs(start_rank - rank) != 1:
            raise IllegalMove("General moves one orthogonal step")

    def _validate_advisor(self, piece: Piece, destination: Position) -> None:
        if not self._in_palace(destination, piece.color):
            raise IllegalMove("Advisor must stay within the palace")
        if not self._is_diagonal_step(piece.position, destination):
            raise IllegalMove("Advisor moves one diagonal step")

    def _validate_elephant(self, piece: Piece, destination: Position) -> None:
        if self._crosses_river(piece.color, destination[1]):
            raise IllegalMove("Elephant cannot cross the river")
        if not self._is_diagonal_jump(piece.position, destination, distance=2):
            raise IllegalMove("Elephant moves two diagonal points")
        eye = self._midpoint(piece.position, destination)
        if self.get_piece(eye):
            raise IllegalMove("Elephant's eye is blocked")

    def _validate_horse(self, piece: Piece, destination: Position) -> None:
        start_file, start_rank = piece.position
        file, rank = destination
        df = abs(start_file - file)
        dr = abs(start_rank - rank)
        if not ((df, dr) in {(1, 2), (2, 1)}):
            raise IllegalMove("Horse moves in an L shape")
        if df == 2:
            leg = (start_file + (file - start_file) // 2, start_rank)
        else:
            leg = (start_file, start_rank + (rank - start_rank) // 2)
        if self.get_piece(leg):
            raise IllegalMove("Horse's leg is blocked")

    def _validate_chariot(self, piece: Piece, destination: Position) -> None:
        if not self._is_straight_line(piece.position, destination):
            raise IllegalMove("Chariot moves in straight lines")
        if not self._path_clear(piece.position, destination):
            raise IllegalMove("Chariot cannot jump over pieces")

    def _validate_cannon(self, piece: Piece, destination: Position) -> None:
        if not self._is_straight_line(piece.position, destination):
            raise IllegalMove("Cannon moves in straight lines")
        between = self._pieces_between(piece.position, destination)
        target = self.get_piece(destination)
        if target:
            if len(between) != 1:
                raise IllegalMove("Cannon must jump exactly one piece to capture")
        else:
            if between:
                raise IllegalMove("Cannon cannot jump without capturing")

    def _validate_soldier(self, piece: Piece, destination: Position) -> None:
        start_file, start_rank = piece.position
        file, rank = destination
        df = file - start_file
        dr = rank - start_rank
        forward = piece.color.forward_direction
        has_crossed = self._has_crossed_river(piece.color, start_rank)
        if dr == forward and df == 0:
            return
        if has_crossed and dr == 0 and abs(df) == 1:
            return
        raise IllegalMove("Soldier can only move forward or sideways after crossing the river")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _validate_general_face_rule(self, piece: Piece, destination: Position) -> None:
        target = self.get_piece(destination)
        clone = self.clone()
        clone.move_piece(piece.position, destination)
        red_general = clone.general_position(Color.RED)
        black_general = clone.general_position(Color.BLACK)
        if red_general and black_general and red_general[0] == black_general[0]:
            if not clone._pieces_between(red_general, black_general):
                raise IllegalMove("Generals cannot face each other directly")
        if target and target.piece_type == PieceType.GENERAL:
            # Captured the opponent's general is always legal (handled above)
            return

    def _validate_no_self_check(self, piece: Piece, destination: Position) -> None:
        clone = self.clone()
        clone.move_piece(piece.position, destination)
        general_pos = clone.general_position(piece.color)
        if general_pos is None:
            return
        if clone._square_attacked(general_pos, self._opponent(piece.color)):
            raise IllegalMove("Move would put general in check")

    def _square_attacked(self, square: Position, attacker: Color) -> bool:
        for piece in tuple(self.pieces()):
            if piece.color != attacker:
                continue
            try:
                self._validate_move_for_attack(piece, square)
            except IllegalMove:
                continue
            else:
                return True
        return False

    def _validate_move_for_attack(self, piece: Piece, destination: Position) -> None:
        target = self.get_piece(destination)
        if target and target.color == piece.color:
            raise IllegalMove("Cannot attack own piece")
        if piece.piece_type == PieceType.GENERAL:
            self._validate_general_for_attack(piece, destination)
        else:
            validator = {
                PieceType.ADVISOR: self._validate_advisor,
                PieceType.ELEPHANT: self._validate_elephant,
                PieceType.HORSE: self._validate_horse,
                PieceType.CHARIOT: self._validate_chariot,
                PieceType.CANNON: self._validate_cannon,
                PieceType.SOLDIER: self._validate_soldier,
            }[piece.piece_type]
            validator(piece, destination)

    def _validate_general_for_attack(self, piece: Piece, destination: Position) -> None:
        start_file, start_rank = piece.position
        file, rank = destination
        if self._in_palace(destination, piece.color) and abs(start_file - file) + abs(start_rank - rank) == 1:
            return
        other_general = self.general_position(self._opponent(piece.color))
        if (
            other_general
            and destination == other_general
            and start_file == file
            and not self._pieces_between(piece.position, destination)
        ):
            return
        raise IllegalMove("General cannot attack that square")

    def _in_palace(self, position: Position, color: Color) -> bool:
        file, rank = position
        if file not in PALACE_FILES:
            return False
        if color == Color.RED:
            return rank in RED_PALACE_RANKS
        return rank in BLACK_PALACE_RANKS

    def _crosses_river(self, color: Color, rank: int) -> bool:
        return rank > RIVER_RANK if color == Color.RED else rank < RIVER_RANK + 1

    def _has_crossed_river(self, color: Color, rank: int) -> bool:
        return rank > RIVER_RANK if color == Color.RED else rank < RIVER_RANK + 1

    def _is_diagonal_step(self, start: Position, end: Position) -> bool:
        return abs(start[0] - end[0]) == 1 and abs(start[1] - end[1]) == 1

    def _is_diagonal_jump(self, start: Position, end: Position, *, distance: int) -> bool:
        return abs(start[0] - end[0]) == distance and abs(start[1] - end[1]) == distance

    def _midpoint(self, start: Position, end: Position) -> Position:
        return ((start[0] + end[0]) // 2, (start[1] + end[1]) // 2)

    def _is_straight_line(self, start: Position, end: Position) -> bool:
        return start[0] == end[0] or start[1] == end[1]

    def _path_clear(self, start: Position, end: Position) -> bool:
        return not self._pieces_between(start, end)

    def _pieces_between(self, start: Position, end: Position) -> List[Piece]:
        pieces: List[Piece] = []
        if start[0] == end[0]:
            step = 1 if end[1] > start[1] else -1
            for rank in range(start[1] + step, end[1], step):
                pos = (start[0], rank)
                piece = self.get_piece(pos)
                if piece:
                    pieces.append(piece)
        elif start[1] == end[1]:
            step = 1 if end[0] > start[0] else -1
            for file in range(start[0] + step, end[0], step):
                pos = (file, start[1])
                piece = self.get_piece(pos)
                if piece:
                    pieces.append(piece)
        return pieces

    def _opponent(self, color: Color) -> Color:
        return Color.RED if color == Color.BLACK else Color.BLACK
