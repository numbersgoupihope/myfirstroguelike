"""Thin curses wrapper: owns the screen/windows and the raw input loop, and
delegates every game-logic decision to :class:`roguelike.session.GameSession`.
"""

import curses

from roguelike import __version__, colors, constants, input_handlers, render_functions, save_handling
from roguelike.game_states import GameStates
from roguelike.session import GameSession


class TerminalTooSmall(Exception):
    pass


class Engine:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        curses.curs_set(0)
        stdscr.keypad(True)
        try:
            # Default ncurses ESCDELAY (~1000ms) makes every "Esc to
            # cancel" feel like it hung. This game uses Esc as a real key,
            # not a multi-byte escape-sequence prefix, so shorten it.
            curses.set_escdelay(25)
        except AttributeError:
            pass
        colors.init_colors()

        height, width = stdscr.getmaxyx()
        if height < constants.SCREEN_HEIGHT or width < constants.SCREEN_WIDTH:
            raise TerminalTooSmall(
                f"Terminal is {width}x{height}; need at least "
                f"{constants.SCREEN_WIDTH}x{constants.SCREEN_HEIGHT}."
            )

        self.map_win = curses.newwin(constants.MAP_HEIGHT, constants.MAP_WIDTH, 0, 0)
        self.stat_win = curses.newwin(
            constants.STAT_PANEL_HEIGHT, constants.STAT_PANEL_WIDTH, 0, constants.MAP_WIDTH
        )
        self.msg_win = curses.newwin(
            constants.MSG_PANEL_HEIGHT, constants.MSG_PANEL_WIDTH, constants.MAP_HEIGHT, 0
        )

        self.session = GameSession()

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def render_all(self):
        stdscr = self.stdscr
        session = self.session
        state = session.state

        if state == GameStates.MAIN_MENU:
            render_functions.render_main_menu(stdscr, save_handling.save_exists(), __version__)
            return
        if state == GameStates.PLAYER_DEAD:
            render_functions.render_game_over_screen(stdscr, session.turn_count, session.dungeon_level)
            return
        if state == GameStates.VICTORY:
            render_functions.render_victory_screen(stdscr, session.turn_count)
            return
        if state == GameStates.EMPTY_HANDED:
            render_functions.render_empty_handed_screen(stdscr, session.turn_count)
            return
        if state == GameStates.HELP_SCREEN:
            render_functions.render_help_screen(stdscr)
            return
        if state == GameStates.CHARACTER_SCREEN:
            render_functions.render_character_screen(stdscr, session.player)
            return
        if state == GameStates.MESSAGE_HISTORY:
            render_functions.render_message_history(stdscr, session.message_log, session.history_scroll)
            return
        if state == GameStates.LEVEL_UP:
            render_functions.render_level_up_menu(stdscr, session.player)
            return
        if state == GameStates.CONFIRM_LEAVE:
            render_functions.render_confirm_dialog(stdscr, "Leave without the Amulet of Yendor?")
            return

        render_functions.render_map(self.map_win, session.game_map, session.visible_tiles)
        render_functions.render_entities(self.map_win, session.entities, session.visible_tiles, session.game_map)
        render_functions.render_stats(
            self.stat_win, session.player, session.dungeon_level, session.turn_count, session.has_amulet()
        )
        render_functions.render_messages(self.msg_win, session.message_log)

        if state == GameStates.TARGETING:
            render_functions.render_cursor(self.map_win, *session.cursor)
            render_functions.render_targeting_prompt(
                self.msg_win, "Move cursor, Enter/t to confirm, Esc to cancel"
            )
            self.msg_win.noutrefresh()

        curses.doupdate()

        if state in (GameStates.SHOW_INVENTORY, GameStates.DROP_INVENTORY):
            verb = "use" if state == GameStates.SHOW_INVENTORY else "drop"
            header = f"Choose an item to {verb} (Esc to cancel)"
            items_desc = [
                session.describe_item_line(chr(ord("a") + i), it)
                for i, it in enumerate(session.player.inventory.items)
            ]
            render_functions.render_inventory_menu(stdscr, header, items_desc)

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def main_loop(self):
        stdscr = self.stdscr
        session = self.session

        while session.state != GameStates.EXIT:
            self.render_all()
            key = stdscr.getch()
            state = session.state

            if state == GameStates.MAIN_MENU:
                action = input_handlers.handle_main_menu_keys(key)
                if action.get("new_game"):
                    session.new_game()
                elif action.get("continue_game") and save_handling.save_exists():
                    try:
                        session.load_from_state(save_handling.load_game())
                    except Exception:
                        save_handling.delete_save()
                elif action.get("quit"):
                    session.state = GameStates.EXIT

            elif state == GameStates.PLAYERS_TURN:
                action = input_handlers.handle_player_turn_keys(key)
                if action:
                    session.process_player_action(action)

            elif state == GameStates.ENEMY_TURN:
                session.run_enemy_turn()

            elif state in (GameStates.SHOW_INVENTORY, GameStates.DROP_INVENTORY):
                action = input_handlers.handle_inventory_keys(key, len(session.player.inventory.items))
                if action.get("exit_menu"):
                    session.state = GameStates.PLAYERS_TURN
                elif "inventory_index" in action:
                    session.handle_inventory_selection(action["inventory_index"])

            elif state == GameStates.TARGETING:
                action = input_handlers.handle_targeting_keys(key)
                if "move_cursor" in action:
                    dx, dy = action["move_cursor"]
                    nx, ny = session.cursor[0] + dx, session.cursor[1] + dy
                    if session.game_map.in_bounds(nx, ny):
                        session.cursor = (nx, ny)
                elif action.get("confirm"):
                    session.resolve_targeting()
                elif action.get("cancel"):
                    session.targeting_item = None
                    session.state = GameStates.PLAYERS_TURN
                    session.message_log.add("Cancelled.", "msg_info")

            elif state == GameStates.LEVEL_UP:
                action = input_handlers.handle_level_up_keys(key)
                if "level_up" in action:
                    session.apply_level_up(action["level_up"])
                    session.state = GameStates.ENEMY_TURN

            elif state == GameStates.CONFIRM_LEAVE:
                action = input_handlers.handle_confirm_keys(key)
                if action.get("confirm"):
                    save_handling.delete_save()
                    session.state = GameStates.EMPTY_HANDED
                elif action.get("cancel"):
                    session.state = GameStates.PLAYERS_TURN

            elif state == GameStates.MESSAGE_HISTORY:
                if key in (27, ord("q")):
                    session.state = session.previous_state
                elif key in (curses.KEY_UP, ord("k")):
                    session.history_scroll = min(
                        session.history_scroll + 1, max(0, len(session.message_log.messages) - 1)
                    )
                elif key in (curses.KEY_DOWN, ord("j")):
                    session.history_scroll = max(session.history_scroll - 1, 0)

            elif state in (GameStates.CHARACTER_SCREEN, GameStates.HELP_SCREEN):
                session.state = session.previous_state

            elif state in (GameStates.PLAYER_DEAD, GameStates.VICTORY, GameStates.EMPTY_HANDED):
                session.reset_to_menu()
