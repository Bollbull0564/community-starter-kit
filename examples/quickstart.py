"""Small demo showing Kung Fu Xiangqi flow."""
from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from kungfu_xiangqi import Game, Color


def main() -> None:
    game = Game()
    print("Initial ready pieces for Red:", len(game.ready_pieces(Color.RED)))
    # Move a red soldier forward in real-time.
    result = game.issue_move((0, 3), (0, 4), current_time=0.0)
    print("Move 1:", result.success, result.message)
    # Soldier now has cooldown.
    result = game.issue_move((0, 4), (0, 5), current_time=0.2)
    print("Move 2 (too soon):", result.success, result.message)
    # Advance time enough for cooldown.
    result = game.issue_move((0, 4), (0, 5), current_time=2.0)
    print("Move 3:", result.success, result.message)


if __name__ == "__main__":
    main()
