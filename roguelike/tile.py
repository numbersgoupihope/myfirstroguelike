"""A single map tile."""


class Tile:
    """One cell of the dungeon.

    ``trap`` holds an optional :class:`~roguelike.components.trap.Trap`
    instance embedded in the floor. Traps start hidden and are only drawn
    once ``trap.discovered`` is True.
    """

    __slots__ = ("blocked", "block_sight", "explored", "trap")

    def __init__(self, blocked, block_sight=None):
        self.blocked = blocked
        # By default if a tile is blocked, it also blocks sight.
        self.block_sight = block_sight if block_sight is not None else blocked
        self.explored = False
        self.trap = None
