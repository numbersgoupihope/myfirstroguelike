# Depths of Yendor -- web edition

A self-contained, single-file browser dungeon crawler. No build step, no
dependencies, no server required -- open `index.html` in any modern
browser (Chrome, Firefox, Safari, Edge) and play.

```bash
# any static file server works, e.g.:
python3 -m http.server 8000 --directory web
# then open http://localhost:8000/
```

or just double-click `index.html`.

## What's in it

Everything is rendered with the Canvas 2D API -- there are no image assets.
Tiles, torches, particles, and every creature (down to the dragon) are drawn
procedurally in code, then lit by a real per-tile lighting model: the
player's carried torch and wall-mounted torches each cast a warm, flickering
radius of light that falls off into darkness, tinting nearby stone gold and
distant stone toward black.

- Procedural dungeons across 10 depths, four biome palettes (crypts, fungal
  hollows, molten reach, the wyrm's throne), with monsters, items, gold and
  hidden traps scaled by depth.
- Turn-based movement is eased into a real tween (start position, end
  position, ~140ms ease-out) rather than snapping tile to tile, with attack
  lunges, hit-flash, particle bursts, floating damage numbers, and screen
  shake layered on top.
- 10 monster archetypes (melee, ranged, poison) up to an ancient dragon
  guarding the Amulet of Yendor. Every one has faintly glowing eyes that
  don't blink and never look away once they've spotted you, and an
  idle motion built from slow uneasy sway plus rare involuntary twitches
  rather than a clean bob.
- **A real combat system, not bump-to-attack.** A stamina bar gates every
  action: light attacks are cheap, heavy attacks (Shift+move) cost more
  stamina, hit harder, and can cleave with an axe; blocking (`F`) consumes
  a one-shot guard that absorbs the next hit; dodging (`V`) spends stamina
  to duck a blow entirely; attacking a monster that hasn't noticed you yet
  is a backstab with a large damage multiplier and near-guaranteed critical
  hit. Weapons (dagger/sword/axe) trade stamina cost, crit chance, and
  backstab multiplier against each other instead of being flat upgrades.
- **The Stalker**: a single, near-unkillable hunter that enters the dungeon
  around depth 3 and persists across floors. It isn't part of the regular
  monster spawn table -- it patrols using the same pathfinding the other
  monsters use, but its detection is probabilistic and driven by ambient
  light and whether you're moving: standing still in a dark tile lets you
  hide from it even in its line of sight. Once it notices you it commits to
  a chase using last-known-position pathing rather than perfect tracking,
  the same trick that makes Alien: Isolation's Xenomorph frightening --
  it's dangerous because it's *persistent*, not because it's strong, and
  fighting it barely scratches it.
- **A sanity meter** that drains in darkness and near the Stalker and
  recovers in light. Low sanity is not cosmetic: it raises the frequency of
  "phantom" glimpses (including full hallucinated monsters that vanish on a
  second look), warps the screen with a distortion filter, and eventually
  starts costing you real HP over time.
- Deliberately unsettling presentation, built on researched horror-design
  principles rather than gore alone: a small, unstable pool of torchlight
  with occasional "gutter" flicker-outs, persistent blood decals, a
  reddening screen pulse and thumping heartbeat under ~30% health, brief
  glimpses of things in the dark that aren't actually anything (the classic
  fear-of-the-unknown trick -- most of what unsettles you here is never
  actually on screen), a deep sub-bass ambient drone that tightens as
  danger closes in, and rare, genuine jump scares (near-silence broken by a
  sudden filtered noise burst, screen flash, and camera shake) rather than
  constant loud noise, because a startle only works against a quiet
  baseline -- with a mute button, because it is a lot.
- Potions, scrolls (including tap-to-target fireball), weapons and armor,
  leveling with a choice of growth on level-up.
- Keyboard (arrows/WASD, `I` for pack, `space` to wait, `F` to block, `V`
  to dodge, Shift+move for a heavy attack, `>`/`<` for stairs) and an
  on-screen d-pad plus action buttons for touch devices; responsive down to
  phone width.
- Save/continue via `localStorage`; permadeath clears it on death or
  leaving the dungeon.

## Why it's a separate edition from the terminal game

The `roguelike/` Python edition is a real curses terminal app and can't
render this kind of art -- a text grid has no lighting, no color gradients,
no animation. This edition reimplements the same core loop (dungeon
generation, turn-based combat, leveling, the Amulet of Yendor win
condition) in JavaScript specifically to be visual, at the cost of a
slightly smaller monster/item roster than the terminal edition's.
