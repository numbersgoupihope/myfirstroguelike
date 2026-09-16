"""Translate curses key codes into semantic action dicts. Kept free of any
curses *window* objects so it's trivially unit-testable with plain ints."""

import curses

MOVE_KEYS = {
    curses.KEY_UP: (0, -1),
    curses.KEY_DOWN: (0, 1),
    curses.KEY_LEFT: (-1, 0),
    curses.KEY_RIGHT: (1, 0),
    ord("k"): (0, -1),
    ord("j"): (0, 1),
    ord("h"): (-1, 0),
    ord("l"): (1, 0),
    ord("y"): (-1, -1),
    ord("u"): (1, -1),
    ord("b"): (-1, 1),
    ord("n"): (1, 1),
    ord("8"): (0, -1),
    ord("2"): (0, 1),
    ord("4"): (-1, 0),
    ord("6"): (1, 0),
    ord("7"): (-1, -1),
    ord("9"): (1, -1),
    ord("1"): (-1, 1),
    ord("3"): (1, 1),
}

CONFIRM_KEYS = (10, 13, curses.KEY_ENTER, ord("t"), ord(" "))
CANCEL_KEYS = (27, ord("q"))


def handle_player_turn_keys(key):
    if key in MOVE_KEYS:
        return {"move": MOVE_KEYS[key]}
    if key in (ord("z"), ord("5"), ord(".")):
        return {"wait": True}
    if key == ord("g") or key == ord(","):
        return {"pickup": True}
    if key == ord("i"):
        return {"show_inventory": True}
    if key == ord("d"):
        return {"drop_inventory": True}
    if key == ord("e"):
        return {"equipment_screen": True}
    if key == ord(">"):
        return {"take_stairs": "down"}
    if key == ord("<"):
        return {"take_stairs": "up"}
    if key == ord("c"):
        return {"character_screen": True}
    if key in (ord("?"), ord("/")):
        return {"help": True}
    if key == ord("m"):
        return {"message_history": True}
    if key == ord("Q"):
        return {"quit": True}
    if key == curses.KEY_RESIZE:
        return {"resize": True}
    return {}


def handle_inventory_keys(key, num_items):
    if key in CANCEL_KEYS:
        return {"exit_menu": True}
    if ord("a") <= key <= ord("z"):
        index = key - ord("a")
        if index < num_items:
            return {"inventory_index": index}
    return {}


def handle_targeting_keys(key):
    if key in MOVE_KEYS:
        return {"move_cursor": MOVE_KEYS[key]}
    if key in CONFIRM_KEYS:
        return {"confirm": True}
    if key == 27:
        return {"cancel": True}
    return {}


def handle_main_menu_keys(key):
    if key in (ord("n"), ord("N")):
        return {"new_game": True}
    if key in (ord("c"), ord("C")):
        return {"continue_game": True}
    if key in (ord("q"), ord("Q"), 27):
        return {"quit": True}
    return {}


def handle_level_up_keys(key):
    if key == ord("s"):
        return {"level_up": "power"}
    if key == ord("v"):
        return {"level_up": "hp"}
    if key == ord("d"):
        return {"level_up": "defense"}
    return {}


def handle_confirm_keys(key):
    if key in (ord("y"), ord("Y")):
        return {"confirm": True}
    if key in (ord("n"), ord("N"), 27):
        return {"cancel": True}
    return {}


def handle_dismiss_keys(key):
    if key == curses.KEY_RESIZE:
        return {"resize": True}
    return {"dismiss": True}
