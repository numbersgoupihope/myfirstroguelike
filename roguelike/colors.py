"""Curses color pair registry.

Everything else in the game refers to colors by semantic name (e.g.
``"player"`` or ``"enemy_atk"``) so that the curses-specific setup lives in
exactly one place. :func:`init_colors` must be called once after
``curses.start_color()`` before :func:`pair` is used.
"""

import curses

# name -> (foreground, background, bold)
_PALETTE = {
    "default": (curses.COLOR_WHITE, curses.COLOR_BLACK, False),
    "wall": (curses.COLOR_WHITE, curses.COLOR_BLACK, False),
    "wall_dark": (curses.COLOR_BLUE, curses.COLOR_BLACK, False),
    "ground": (curses.COLOR_WHITE, curses.COLOR_BLACK, False),
    "ground_dark": (curses.COLOR_BLUE, curses.COLOR_BLACK, False),
    "player": (curses.COLOR_WHITE, curses.COLOR_BLACK, True),
    "stairs": (curses.COLOR_WHITE, curses.COLOR_BLACK, True),
    "trap_hidden": (curses.COLOR_WHITE, curses.COLOR_BLACK, False),
    "trap_visible": (curses.COLOR_MAGENTA, curses.COLOR_BLACK, True),
    "amulet": (curses.COLOR_YELLOW, curses.COLOR_BLACK, True),
    "monster_weak": (curses.COLOR_GREEN, curses.COLOR_BLACK, False),
    "monster_normal": (curses.COLOR_YELLOW, curses.COLOR_BLACK, False),
    "monster_tough": (curses.COLOR_RED, curses.COLOR_BLACK, True),
    "monster_boss": (curses.COLOR_MAGENTA, curses.COLOR_BLACK, True),
    "item_potion": (curses.COLOR_MAGENTA, curses.COLOR_BLACK, False),
    "item_scroll": (curses.COLOR_CYAN, curses.COLOR_BLACK, False),
    "item_weapon": (curses.COLOR_WHITE, curses.COLOR_BLACK, True),
    "item_armor": (curses.COLOR_BLUE, curses.COLOR_BLACK, True),
    "item_food": (curses.COLOR_YELLOW, curses.COLOR_BLACK, False),
    "item_gold": (curses.COLOR_YELLOW, curses.COLOR_BLACK, True),
    "msg_info": (curses.COLOR_WHITE, curses.COLOR_BLACK, False),
    "msg_warning": (curses.COLOR_YELLOW, curses.COLOR_BLACK, False),
    "msg_bad": (curses.COLOR_RED, curses.COLOR_BLACK, True),
    "msg_good": (curses.COLOR_GREEN, curses.COLOR_BLACK, True),
    "msg_crit": (curses.COLOR_MAGENTA, curses.COLOR_BLACK, True),
    "hp_full": (curses.COLOR_GREEN, curses.COLOR_BLACK, False),
    "hp_mid": (curses.COLOR_YELLOW, curses.COLOR_BLACK, False),
    "hp_low": (curses.COLOR_RED, curses.COLOR_BLACK, True),
    "bar_bg": (curses.COLOR_WHITE, curses.COLOR_BLUE, False),
    "bar_empty": (curses.COLOR_WHITE, curses.COLOR_BLACK, False),
    "title": (curses.COLOR_YELLOW, curses.COLOR_BLACK, True),
    "highlight": (curses.COLOR_BLACK, curses.COLOR_WHITE, True),
    "hunger_ok": (curses.COLOR_WHITE, curses.COLOR_BLACK, False),
    "hunger_hungry": (curses.COLOR_YELLOW, curses.COLOR_BLACK, False),
    "hunger_starving": (curses.COLOR_RED, curses.COLOR_BLACK, True),
}

_pair_ids = {}
_initialized = False
_has_color = False


def init_colors():
    """Register curses color pairs for every entry in the palette.

    Safe to call even on terminals without color support -- in that case
    :func:`pair` degrades to plain ``curses.A_NORMAL``/``curses.A_BOLD``.
    """
    global _initialized, _has_color
    _has_color = curses.has_colors()
    if _has_color:
        try:
            curses.start_color()
        except curses.error:
            pass
        try:
            curses.use_default_colors()
        except curses.error:
            pass
        next_id = 1
        for name, (fg, bg, _bold) in _PALETTE.items():
            try:
                curses.init_pair(next_id, fg, bg)
            except curses.error:
                # Terminal doesn't support this many pairs / colors.
                continue
            _pair_ids[name] = next_id
            next_id += 1
    _initialized = True


def pair(name):
    """Return the curses attribute to use for a semantic color name."""
    if not _initialized:
        return curses.A_NORMAL
    bold = _PALETTE.get(name, (None, None, False))[2]
    attr = curses.A_BOLD if bold else curses.A_NORMAL
    if _has_color and name in _pair_ids:
        attr |= curses.color_pair(_pair_ids[name])
    return attr


def hp_color(hp_ratio):
    if hp_ratio > 0.6:
        return "hp_full"
    if hp_ratio > 0.3:
        return "hp_mid"
    return "hp_low"
