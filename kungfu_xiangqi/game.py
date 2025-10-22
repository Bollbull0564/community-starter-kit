"""Real-time Kung Fu Xiangqi game state."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

from .board import Board, IllegalMove, Move
from .pieces import Color, Piece


@dataclass
class MoveResult:
    """Outcome of an attempted move."""

    success: bool
    message: str
    move: Optional[Move] = None


class Game:
    """Manage Kung Fu Xiangqi gameplay with per-piece cooldowns."""

    def __init__(self, board: Optional[Board] = None) -> None:
        self.board = board or Board()
        self.time = 0.0

    def advance_time(self, new_time: float) -> None:
        if new_time < self.time:
            raise ValueError("Time cannot go backwards")
        delta = new_time - self.time
        if delta <= 0:
            return
        for piece in self.board.pieces():
            piece.advance_cooldown(delta)
        self.time = new_time

    def issue_move(self, start: Tuple[int, int], end: Tuple[int, int], current_time: float) -> MoveResult:
        self.advance_time(current_time)
        piece = self.board.get_piece(start)
        if piece is None:
            return MoveResult(False, "No piece at the starting square")
        if not piece.is_ready:
            return MoveResult(False, "Piece is still on cooldown")
        try:
            self.board.validate_move(piece, end)
            move = self.board.move_piece(start, end)
        except IllegalMove as exc:
            return MoveResult(False, str(exc))
        move.piece.reset_cooldown()
        return MoveResult(True, "Move executed", move)

    def ready_pieces(self, color: Color) -> Tuple[Piece, ...]:
        return tuple(piece for piece in self.board.pieces() if piece.color == color and piece.is_ready)

    def winner(self) -> Optional[Color]:
        red_general = self.board.general_position(Color.RED)
        black_general = self.board.general_position(Color.BLACK)
        if red_general is None:
            return Color.BLACK
        if black_general is None:
            return Color.RED
        return None
