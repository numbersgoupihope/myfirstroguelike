"""All curses drawing lives here. Every helper is defensive about writing
past window edges (curses raises on the bottom-right cell of a window), so
callers never need to think about it."""

import curses

from roguelike import colors, constants
from roguelike.components.equippable import EquipmentSlots

TRAP_CHARS = {
    "dart": "^",
    "pit": "v",
    "poison_gas": ":",
    "confusion": "?",
    "alarm": "!",
}


def safe_addstr(win, y, x, text, attr=curses.A_NORMAL):
    try:
        max_y, max_x = win.getmaxyx()
        if y < 0 or y >= max_y or x >= max_x:
            return
        if x < 0:
            text = text[-x:]
            x = 0
        text = text[: max(0, max_x - x)]
        if not text:
            return
        win.addstr(y, x, text, attr)
    except curses.error:
        pass


def safe_addch(win, y, x, ch, attr=curses.A_NORMAL):
    try:
        max_y, max_x = win.getmaxyx()
        if 0 <= y < max_y and 0 <= x < max_x:
            win.addch(y, x, ch, attr)
    except curses.error:
        pass


def render_map(win, game_map, visible_tiles):
    win.erase()
    for y in range(game_map.height):
        for x in range(game_map.width):
            tile = game_map.tiles[y][x]
            visible = (x, y) in visible_tiles
            if visible:
                tile.explored = True
            elif not tile.explored:
                continue

            if tile.trap is not None and tile.trap.discovered:
                ch = TRAP_CHARS.get(tile.trap.kind, "^")
                color = colors.pair("trap_visible" if visible else "wall_dark")
            elif tile.blocked:
                ch = "#"
                color = colors.pair("wall" if visible else "wall_dark")
            else:
                ch = "."
                color = colors.pair("ground" if visible else "ground_dark")
            safe_addch(win, y, x, ch, color)


def render_entities(win, entities, visible_tiles, game_map):
    for entity in sorted(entities, key=lambda e: e.render_order.value):
        visible = (entity.x, entity.y) in visible_tiles
        if not visible:
            if not (entity.always_visible and game_map.tiles[entity.y][entity.x].explored):
                continue
        safe_addch(win, entity.y, entity.x, entity.char, colors.pair(entity.color))
    win.noutrefresh()


def render_cursor(win, x, y):
    safe_addch(win, y, x, "X", colors.pair("highlight"))
    win.noutrefresh()


def _bar_string(width, value, maximum):
    if maximum <= 0:
        filled = 0
    else:
        filled = max(0, min(width, round(width * max(0, value) / maximum)))
    return "#" * filled + "-" * (width - filled)


def render_stats(win, player, dungeon_level, turn_count, amulet_taken):
    win.erase()
    width = constants.STAT_PANEL_WIDTH
    row = 0

    def line(text, attr=None, indent=0):
        nonlocal row
        safe_addstr(win, row, indent, text, attr if attr is not None else colors.pair("default"))
        row += 1

    line("Depths of Yendor", colors.pair("title"))
    line("-" * (width - 1))
    fighter = player.fighter
    level = player.level
    line(f"{player.name}  Lv.{level.current_level}")
    row += 1
    line("HP", colors.pair("default"))
    line(_bar_string(width - 1, fighter.hp, fighter.max_hp), colors.pair(colors.hp_color(fighter.hp / max(1, fighter.max_hp))))
    line(f"{fighter.hp}/{fighter.max_hp}")
    row += 1
    xp_needed = level.experience_to_next_level
    line("XP", colors.pair("default"))
    line(_bar_string(width - 1, level.current_xp, xp_needed), colors.pair("hp_mid"))
    line(f"{level.current_xp}/{xp_needed}")
    row += 1
    line(f"Pwr:{fighter.power}  Def:{fighter.defense}")
    line(f"Depth: {dungeon_level}")
    line(f"Gold: {getattr(player, 'gold', 0)}")

    hunger = player.hunger
    if hunger is not None:
        state = hunger.state
        color = {
            "ok": colors.pair("hunger_ok"),
            "hungry": colors.pair("hunger_hungry"),
            "starving": colors.pair("hunger_starving"),
        }[state]
        line(f"Hunger: {state.capitalize()}", color)

    if amulet_taken:
        line("Amulet carried!", colors.pair("amulet"))

    row += 1
    line("-- Equipment --")
    equipment = player.equipment
    slot_labels = {
        EquipmentSlots.WEAPON: "Wpn",
        EquipmentSlots.ARMOR: "Arm",
        EquipmentSlots.SHIELD: "Sld",
    }
    for slot, label in slot_labels.items():
        item = equipment.slots.get(slot) if equipment else None
        line(f"{label}: {item.name if item else '(none)'}")

    status = player.status_effects
    if status and (status.is_poisoned or status.is_confused):
        row += 1
        line("-- Status --")
        if status.is_poisoned:
            line(f"Poisoned ({status.poison_turns})", colors.pair("msg_bad"))
        if status.is_confused:
            line(f"Confused ({status.confusion_turns})", colors.pair("msg_warning"))

    win.noutrefresh()


def render_messages(win, message_log):
    win.erase()
    height = constants.MSG_PANEL_HEIGHT
    recent = message_log.messages[-height:]
    for i, message in enumerate(recent):
        safe_addstr(win, i, 0, message.text, colors.pair(message.color))
    win.noutrefresh()


def render_targeting_prompt(win, text):
    safe_addstr(win, 0, 0, text, colors.pair("msg_warning"))
    win.noutrefresh()


def center_x(width, text):
    return max(0, (width - len(text)) // 2)


def render_main_menu(stdscr, has_save, version):
    stdscr.erase()
    h, w = stdscr.getmaxyx()
    title = "DEPTHS OF YENDOR"
    subtitle = "a roguelike"
    lines = [
        "",
        "",
        title,
        subtitle,
        "",
        "",
        "(N) New Game",
    ]
    if has_save:
        lines.append("(C) Continue")
    lines.append("(Q) Quit")
    lines.append("")
    lines.append(f"v{version}")

    start_y = max(0, h // 2 - len(lines) // 2 - 3)
    for i, text in enumerate(lines):
        attr = colors.pair("title") if text in (title,) else colors.pair("default")
        safe_addstr(stdscr, start_y + i, center_x(w, text), text, attr)
    stdscr.refresh()


def render_inventory_menu(stdscr, header, items, empty_message="(empty)"):
    # Deliberately does not erase stdscr: this is an overlay on top of the
    # already-drawn map/stat/message panels, not a full-screen replacement.
    # (Erasing stdscr here without a matching stdscr.refresh() leaves it
    # dirty, and ncurses silently flushes that blank buffer -- wiping this
    # very box -- the next time stdscr.getch() is called.)
    # Centered over the map pane specifically (not the full screen) so it
    # reads as a dungeon-view overlay instead of colliding with the stat
    # sidebar off to the right.
    box_width = min(constants.MAP_WIDTH - 4, 56)
    box_height = min(constants.MAP_HEIGHT - 2, len(items) + 4)
    box_height = max(box_height, 5)
    start_y = max(0, (constants.MAP_HEIGHT - box_height) // 2)
    start_x = max(0, (constants.MAP_WIDTH - box_width) // 2)

    win = curses.newwin(box_height, box_width, start_y, start_x)
    win.box()
    safe_addstr(win, 0, 2, f" {header} ", colors.pair("title"))

    if not items:
        safe_addstr(win, 2, 2, empty_message, colors.pair("default"))
    else:
        for i, text in enumerate(items[: box_height - 3]):
            safe_addstr(win, i + 1, 2, text, colors.pair("default"))

    safe_addstr(win, box_height - 1, 2, "[Esc] cancel", colors.pair("msg_info"))
    win.refresh()


def render_character_screen(stdscr, player):
    stdscr.erase()
    h, w = stdscr.getmaxyx()
    level = player.level
    fighter = player.fighter
    lines = [
        "Character Sheet",
        "-" * 24,
        f"Level: {level.current_level}",
        f"Experience: {level.current_xp}",
        f"Next level: {level.experience_to_next_level}",
        "",
        f"Max HP: {fighter.max_hp}",
        f"Power: {fighter.power}",
        f"Defense: {fighter.defense}",
        "",
        f"Gold: {getattr(player, 'gold', 0)}",
        "",
        "Press any key to continue.",
    ]
    for i, text in enumerate(lines):
        safe_addstr(stdscr, 2 + i, 4, text, colors.pair("default"))
    stdscr.refresh()


def render_level_up_menu(stdscr, player):
    stdscr.erase()
    fighter = player.fighter
    lines = [
        "Level up! Choose an improvement:",
        "",
        f"(s) Power        (current: {fighter.power})",
        f"(v) Vitality/HP  (current: {fighter.max_hp})",
        f"(d) Defense      (current: {fighter.defense})",
    ]
    for i, text in enumerate(lines):
        safe_addstr(stdscr, 2 + i, 4, text, colors.pair("title") if i == 0 else colors.pair("default"))
    stdscr.refresh()


def render_help_screen(stdscr):
    stdscr.erase()
    lines = [
        "Depths of Yendor -- Help",
        "-" * 32,
        "Movement: arrow keys, hjkl, or numpad (y/u/b/n for diagonals)",
        "z / . / 5   Wait a turn",
        "g / ,       Pick up item",
        "i           Inventory / use item",
        "d           Drop item",
        ">           Descend stairs",
        "<           Ascend stairs (or leave the dungeon, on level 1)",
        "c           Character screen",
        "m           Message history",
        "Q           Save and quit",
        "?           This help screen",
        "",
        "Find the Amulet of Yendor at the bottom of the dungeon and",
        "carry it back to the surface to win. Good luck.",
        "",
        "Press any key to continue.",
    ]
    for i, text in enumerate(lines):
        attr = colors.pair("title") if i == 0 else colors.pair("default")
        safe_addstr(stdscr, 1 + i, 2, text, attr)
    stdscr.refresh()


def render_message_history(stdscr, message_log, scroll):
    stdscr.erase()
    h, w = stdscr.getmaxyx()
    visible_lines = max(1, h - 3)
    messages = message_log.messages
    start = max(0, len(messages) - visible_lines - scroll)
    end = start + visible_lines
    page = messages[start:end]

    safe_addstr(stdscr, 0, 2, "Message History (Up/Down to scroll, Esc to exit)", colors.pair("title"))
    for i, message in enumerate(page):
        safe_addstr(stdscr, 2 + i, 2, message.text, colors.pair(message.color))
    stdscr.refresh()


def render_game_over_screen(stdscr, turn_count, dungeon_level):
    stdscr.erase()
    h, w = stdscr.getmaxyx()
    lines = [
        "YOU HAVE DIED",
        "",
        f"You perished on dungeon level {dungeon_level}.",
        f"Turns survived: {turn_count}",
        "",
        "Press any key to return to the main menu.",
    ]
    start_y = max(0, h // 2 - len(lines) // 2)
    for i, text in enumerate(lines):
        attr = colors.pair("msg_crit") if i == 0 else colors.pair("default")
        safe_addstr(stdscr, start_y + i, center_x(w, text), text, attr)
    stdscr.refresh()


def render_victory_screen(stdscr, turn_count):
    stdscr.erase()
    h, w = stdscr.getmaxyx()
    lines = [
        "*** YOU ESCAPED WITH THE AMULET OF YENDOR ***",
        "",
        f"Turns taken: {turn_count}",
        "",
        "You are victorious. Press any key to return to the main menu.",
    ]
    start_y = max(0, h // 2 - len(lines) // 2)
    for i, text in enumerate(lines):
        attr = colors.pair("amulet") if i == 0 else colors.pair("default")
        safe_addstr(stdscr, start_y + i, center_x(w, text), text, attr)
    stdscr.refresh()


def render_empty_handed_screen(stdscr, turn_count):
    stdscr.erase()
    h, w = stdscr.getmaxyx()
    lines = [
        "You leave the dungeon empty-handed.",
        "",
        f"Turns taken: {turn_count}",
        "Your quest for the Amulet of Yendor remains unfinished.",
        "",
        "Press any key to return to the main menu.",
    ]
    start_y = max(0, h // 2 - len(lines) // 2)
    for i, text in enumerate(lines):
        attr = colors.pair("msg_warning") if i == 0 else colors.pair("default")
        safe_addstr(stdscr, start_y + i, center_x(w, text), text, attr)
    stdscr.refresh()


def render_confirm_dialog(stdscr, text):
    stdscr.erase()
    h, w = stdscr.getmaxyx()
    lines = [text, "", "(Y)es / (N)o"]
    start_y = max(0, h // 2 - 1)
    for i, line_text in enumerate(lines):
        safe_addstr(stdscr, start_y + i, center_x(w, line_text), line_text, colors.pair("msg_warning"))
    stdscr.refresh()
