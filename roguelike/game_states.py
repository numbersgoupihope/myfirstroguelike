from enum import Enum, auto


class GameStates(Enum):
    MAIN_MENU = auto()
    PLAYERS_TURN = auto()
    ENEMY_TURN = auto()
    PLAYER_DEAD = auto()
    SHOW_INVENTORY = auto()
    DROP_INVENTORY = auto()
    TARGETING = auto()
    LEVEL_UP = auto()
    CHARACTER_SCREEN = auto()
    HELP_SCREEN = auto()
    MESSAGE_HISTORY = auto()
    CONFIRM_LEAVE = auto()
    VICTORY = auto()
    EMPTY_HANDED = auto()
    EXIT = auto()
