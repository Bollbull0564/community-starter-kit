# Kung Fu Xiangqi

"Kung Fu Chess" reimagined for Chinese chess (Xiangqi). This repository currently
contains a pure-Python engine that models real-time play by giving every piece
its own cooldown after moving. It focuses on accurate Xiangqi movement rules so
that you can experiment with fast-paced variants, bots, or simulations.

## Features

- Full board representation with standard Xiangqi starting position.
- Rule enforcement for all pieces including horses with blocked legs and
  cannons that must jump to capture.
- General face-off detection and self-check prevention to keep moves legal.
- Real-time `Game` manager that tracks a global clock and per-piece cooldowns.
- Simple example script (`examples/quickstart.py`) demonstrating how to drive
the engine.

## Getting Started

This project targets Python 3.10+. Run the quick start example directly:

```bash
python examples/quickstart.py
```

Feel free to build on top of the `Game` class to add networking, graphical
interfaces, or AI opponents for a full Kung Fu Xiangqi experience.
