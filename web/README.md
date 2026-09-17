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
- Deliberately unsettling presentation: a small, unstable pool of torchlight
  with occasional "gutter" flicker-outs, persistent blood decals where
  things have died or bled, a reddening screen pulse and thumping heartbeat
  under ~30% health, brief glimpses of eyes in the dark that aren't
  actually anything, and a bed of dissonant WebAudio drone/noise instead of
  clean tones -- with a mute button, because it is a lot.
- Potions, scrolls (including tap-to-target fireball), weapons and armor,
  leveling with a choice of growth on level-up.
- Keyboard (arrows/WASD, `I` for pack, `space` to wait, `>`/`<` for stairs)
  and an on-screen d-pad for touch devices; responsive down to phone width.
- Save/continue via `localStorage`; permadeath clears it on death or
  leaving the dungeon.

## Why it's a separate edition from the terminal game

The `roguelike/` Python edition is a real curses terminal app and can't
render this kind of art -- a text grid has no lighting, no color gradients,
no animation. This edition reimplements the same core loop (dungeon
generation, turn-based combat, leveling, the Amulet of Yendor win
condition) in JavaScript specifically to be visual, at the cost of a
slightly smaller monster/item roster than the terminal edition's.
