# Depths of Yendor

A complete terminal roguelike, built from scratch in pure-stdlib Python
(`curses` only -- no dependencies to install to play). Descend through ten
procedurally generated dungeon levels, fight your way past a growing bestiary,
loot gear and potions, and retrieve the Amulet of Yendor from the ancient
dragon that guards it -- then survive the climb back to the surface with it
in hand.

## Features

- **Procedural dungeons** -- every level is a fresh layout of rooms and
  corridors, fully connected, with difficulty (monster/item tables, trap
  density) scaling by depth.
- **Real field-of-view** -- an from-scratch recursive shadowcasting
  implementation; the map is remembered once explored but only currently
  visible tiles show monsters and lighting.
- **Tactical, seedable combat** -- hit chance and damage both come from a
  pure, testable formula (`roguelike/combat.py`) so power vs. defense
  tradeoffs matter.
- **17 monster types** from giant rats to an ancient dragon, with distinct
  behaviours: melee chasers, ranged skirmishers that kite you, stationary
  ambushers, a poison-biting spider, and a life-draining vampire.
- **Full itemization** -- potions (healing, strength, cleansing, and a
  cursed one), scrolls (lightning bolt, fireball, confusion, teleport,
  magic mapping), weapons, armor, shields, food, and gold.
- **Equipment & leveling** -- three equipment slots with stat bonuses, and
  an XP/level-up system that lets you choose power, HP, or defense on
  level-up.
- **Hunger clock** -- eat food or starve, with escalating consequences.
- **Hidden traps** -- darts, pits, poison gas, confusion runes, and alarms,
  discovered by (unluckily) triggering them.
- **Status effects** -- poison and confusion apply to monsters and the
  player alike.
- **Permadeath with save/load** -- quit and resume a single in-progress
  run; the save is deleted on death, victory, or leaving the dungeon.
- **A real win condition** -- carry the Amulet of Yendor from dungeon level
  10 back to level 1 to win. Leaving early without it ends the run too, but
  unfinished.

## Playing

Requires only Python 3.9+ (uses the standard library's `curses`, which
ships with Python on Linux and macOS; on Windows install `windows-curses`
first: `pip install windows-curses`). Needs a terminal at least 80x24.

```bash
python3 main.py
```

or, after an editable install (`pip install -e .`):

```bash
yendor
```

### Controls

| Key(s)                  | Action                                   |
|--------------------------|-------------------------------------------|
| Arrow keys / `hjkl` / numpad | Move / attack (8-directional)         |
| `y u b n`                | Diagonal movement                        |
| `z`, `.`, `5`             | Wait a turn                              |
| `g`, `,`                  | Pick up item (or gold)                   |
| `i`                       | Inventory -- use or equip an item        |
| `d`                       | Drop an item                             |
| `>`                       | Descend stairs                           |
| `<`                       | Ascend stairs (or leave the dungeon on level 1) |
| `c`                       | Character screen                         |
| `m`                       | Message history                          |
| `?`                       | Help screen                              |
| `Q`                       | Save and quit                            |

When using a targeted scroll, move the cursor and press Enter/`t` to
confirm or Esc to cancel.

## Running the tests

```bash
pip install pytest pyte   # pyte is only needed if you also want the
                           # visual pyte-rendering scratch scripts; pytest
                           # alone is enough for the test suite
python3 -m pytest
```

The suite has ~90 tests split two ways:

- **Headless logic tests** (`test_fov.py`, `test_pathfinding.py`,
  `test_game_map.py`, `test_combat.py`, `test_components.py`,
  `test_item_functions.py`, `test_world_gen.py`, `test_death_functions.py`,
  `test_session.py`) exercise dungeon generation, FOV, pathfinding, combat
  math, every component, every item effect, and the full turn-based game
  loop directly through `roguelike.session.GameSession` -- no curses
  involved, so they run in milliseconds.
- **`test_smoke_pty.py`** drives the actual `main.py` process end-to-end
  over a real pseudo-terminal (menus, movement, inventory, help, character
  screen, save-and-quit, and a too-small-terminal error path), which is the
  only way to exercise the curses rendering layer itself.

## Architecture

```
roguelike/
  entity.py, tile.py, rectangle.py    -- core data structures
  game_map.py                          -- room/corridor dungeon generation
  fov.py                                -- recursive shadowcasting
  pathfinding.py                        -- BFS "scent map" for monster AI
  combat.py                             -- pure hit/damage formula
  components/                           -- fighter, ai, inventory, item,
                                           equipment, level, hunger,
                                           status_effects, trap, stairs
  monster_data.py, item_data.py         -- entity factories
  item_functions.py                     -- scroll/potion effects
  world_gen.py                          -- depth-scaled population tables
  death_functions.py                    -- corpse conversion / xp
  message_log.py, game_states.py        -- support types
  session.py                            -- GameSession: all game logic,
                                           zero curses dependency
  engine.py                             -- thin curses wrapper: windows,
                                           input loop, rendering, delegates
                                           every decision to GameSession
  render_functions.py, input_handlers.py, colors.py
  save_handling.py                      -- pickle-based single-slot save
main.py / roguelike/main.py             -- curses bootstrap
```

The `session.py` / `engine.py` split is deliberate: `GameSession` holds
100% of the game rules and state with no curses dependency, so the entire
game -- combat, inventory, dungeon generation, save/load, win/loss
conditions -- is unit-testable without a terminal. `Engine` is a thin
adapter that owns the curses windows, reads keys, and translates
`GameSession` state into drawing calls.

## Known simplifications

A few classic-roguelike features were deliberately left out to keep this a
finished, well-tested game rather than a sprawling half-built one:

- Items are never "unidentified" -- what you see is what it is.
- Previously-visited floors are not persisted; they regenerate if you
  return (matching many lighter roguelikes, unlike NetHack/Rogue's
  persistent levels).
- No "search" command for traps -- they're discovered by triggering them.
