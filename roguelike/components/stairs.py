"""Marks an Entity as a staircase connecting dungeon levels."""


class Stairs:
    def __init__(self, floor, direction):
        # direction is "down" or "up"
        self.floor = floor
        self.direction = direction
        self.owner = None
