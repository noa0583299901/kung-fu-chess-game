# Kung Fu Chess

Real-time chess variant where all pieces move simultaneously — no turns.

## How to Play

```bash
python -m kungfu_chess.app_gui
```

**Controls:**
- **Click** a piece to select it (green highlight)
- **Click** a destination to move
- **Double-click** a piece to jump (airborne — captures enemies who arrive)
- **R** — reset game
- **ESC / Q** — quit

## Rules

- No turns — both sides move at the same time
- Movement takes time (1 cell = 1 second)
- 2-second cooldown after each move (yellow overlay)
- 1-second cooldown after landing from a jump
- Pawn promotes to Queen at the last row
- Capturing the King ends the game
- Late arrival captures early arrival (collision)

## Architecture

```
kungfu_chess/
  model/         — Position, Piece, Board, GameState
  rules/         — MovementStrategy (ABC), PieceRuleRegistry, RuleEngine, GameConditions
  realtime/      — Motion, RealTimeArbiter (simultaneous movement, collisions)
  engine/        — GameEngine (DI, Observer pattern, application service)
  input/         — BoardMapper, Controller (selection + click dispatch)
  io/            — BoardParser, BoardPrinter (text I/O adapters)
  view/          — Renderer (Img library, sprites, animations)
  texttests/     — ScriptParser, ScriptRunner (DSL test harness)
  constants.py   — All configuration values
  app_gui.py     — GUI entry point (OpenCV fullscreen)
  app.py         — Text DSL entry point
```

## Design Patterns

- **Strategy** — MovementStrategy per piece type + PieceRuleRegistry
- **Observer** — GameEngine notifies observers on move/capture/game-over
- **DI** — GameEngine accepts arbiter, validate_move_fn, win_condition, promotion_rule
- **Registry** — PIECE_RULE_REGISTRY maps piece kind to strategy instance

## Tests

```bash
pip install pytest pytest-cov
python -m pytest tests/ --cov=kungfu_chess
```

123 tests | 99% coverage

## Requirements

- Python 3.10+
- opencv-python (`pip install opencv-python`)
- CTD26 assets folder (sprites + board.png)
