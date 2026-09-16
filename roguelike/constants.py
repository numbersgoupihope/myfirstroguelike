"""Global game constants and tuning knobs."""

# --- Window / layout ---
# Sized to fit inside the ubiquitous 80x24 default terminal.
STAT_PANEL_WIDTH = 20
MAP_WIDTH = 60
SCREEN_WIDTH = MAP_WIDTH + STAT_PANEL_WIDTH  # 80

MSG_PANEL_HEIGHT = 4
MAP_HEIGHT = 20
STAT_PANEL_HEIGHT = MAP_HEIGHT

MSG_PANEL_WIDTH = SCREEN_WIDTH
SCREEN_HEIGHT = MAP_HEIGHT + MSG_PANEL_HEIGHT  # 24

# --- Dungeon generation ---
ROOM_MAX_SIZE = 8
ROOM_MIN_SIZE = 4
MAX_ROOMS = 30

MAX_MONSTERS_PER_ROOM_BASE = 2
MAX_ITEMS_PER_ROOM_BASE = 2

# Depth at which the Amulet of Yendor is found. Grab it and climb back to
# depth 1 to win the game.
AMULET_DEPTH = 10

# --- FOV ---
FOV_RADIUS = 8

# --- Player ---
PLAYER_BASE_HP = 30
PLAYER_BASE_DEFENSE = 1
PLAYER_BASE_POWER = 4

HUNGER_MAX = 1000
HUNGER_HUNGRY_THRESHOLD = 300
HUNGER_STARVING_THRESHOLD = 50
STARVING_DAMAGE_PERIOD = 10  # take damage every N turns while starving

# --- Leveling ---
LEVEL_UP_BASE = 200
LEVEL_UP_FACTOR = 150
LEVEL_SCREEN_WIDTH = 40

# --- Inventory ---
INVENTORY_CAPACITY = 26  # one per letter, a-z

# --- Misc ---
SAVE_FILE_NAME = ".yendor_save.dat"
