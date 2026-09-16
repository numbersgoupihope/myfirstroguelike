"""curses bootstrap: sets up the terminal, builds the Engine, and hands off
to its main loop."""

import curses
import sys

from roguelike import constants
from roguelike.engine import Engine, TerminalTooSmall


def _run(stdscr):
    engine = Engine(stdscr)
    engine.main_loop()


def main():
    try:
        curses.wrapper(_run)
    except TerminalTooSmall as exc:
        print(str(exc))
        print(
            "Please resize your terminal to at least "
            f"{constants.SCREEN_WIDTH}x{constants.SCREEN_HEIGHT} and try again."
        )
        sys.exit(1)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
