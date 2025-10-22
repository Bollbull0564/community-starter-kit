"""Definitions for Kung Fu Xiangqi pieces."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Tuple


Position = Tuple[int, int]


class Color(str, Enum):
    """Color of a piece."""

    RED = "red"
    BLACK = "black"

    @property
    def forward_direction(self) -> int:
        """Return the forward direction on the board."""
        return 1 if self is Color.RED else -1

    @property
    def home_ranks(self) -> range:
        """Return the ranks considered the home side."""
        return range(0, 5) if self is Color.RED else range(5, 10)


class PieceType(str, Enum):
    """Enumerates all Xiangqi piece types."""

    GENERAL = "general"
    ADVISOR = "advisor"
    ELEPHANT = "elephant"
    HORSE = "horse"
    CHARIOT = "chariot"
    CANNON = "cannon"
    SOLDIER = "soldier"

    @property
    def base_cooldown(self) -> float:
        """Return the default cooldown duration in seconds."""
        cooldowns: Dict["PieceType", float] = {
            PieceType.GENERAL: 4.0,
            PieceType.ADVISOR: 3.5,
            PieceType.ELEPHANT: 3.5,
            PieceType.HORSE: 2.5,
            PieceType.CHARIOT: 1.8,
            PieceType.CANNON: 2.0,
            PieceType.SOLDIER: 1.5,
        }
        return cooldowns[self]


@dataclass
class Piece:
    """Represents a single piece on the board."""

    color: Color
    piece_type: PieceType
    position: Position
    cooldown_remaining: float = field(default=0.0)

    def copy(self) -> "Piece":
        return Piece(
            color=self.color,
            piece_type=self.piece_type,
            position=self.position,
            cooldown_remaining=self.cooldown_remaining,
        )

    def reset_cooldown(self) -> None:
        self.cooldown_remaining = self.piece_type.base_cooldown

    def advance_cooldown(self, delta: float) -> None:
        self.cooldown_remaining = max(0.0, self.cooldown_remaining - delta)

    @property
    def is_ready(self) -> bool:
        return self.cooldown_remaining <= 0

    def __str__(self) -> str:  # pragma: no cover - for debugging
        return f"{self.color.value[0].upper()}{self.piece_type.value[0].upper()}@{self.position}"
