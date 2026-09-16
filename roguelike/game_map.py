"""Dungeon layout: tile grid, room placement, and corridor carving."""

import random

from roguelike.rectangle import Rect
from roguelike.tile import Tile


class GameMap:
    def __init__(self, width, height, dungeon_level=1):
        self.width = width
        self.height = height
        self.dungeon_level = dungeon_level
        self.tiles = [[Tile(True) for _ in range(width)] for _ in range(height)]
        self.rooms = []
        self.upstairs_pos = None
        self.downstairs_pos = None

    def in_bounds(self, x, y):
        return 0 <= x < self.width and 0 <= y < self.height

    def is_blocked(self, x, y):
        if not self.in_bounds(x, y):
            return True
        return self.tiles[y][x].blocked

    def _carve(self, x, y):
        self.tiles[y][x].blocked = False
        self.tiles[y][x].block_sight = False

    def create_room(self, room):
        for y in range(room.y1 + 1, room.y2):
            for x in range(room.x1 + 1, room.x2):
                self._carve(x, y)

    def create_h_tunnel(self, x1, x2, y):
        for x in range(min(x1, x2), max(x1, x2) + 1):
            self._carve(x, y)

    def create_v_tunnel(self, y1, y2, x):
        for y in range(min(y1, y2), max(y1, y2) + 1):
            self._carve(x, y)

    def make_map(self, max_rooms, room_min_size, room_max_size, player, rng=None):
        """Carve rooms connected by corridors, dropping the player in the
        first room. Returns the placed :class:`Rect` list for callers that
        want to populate rooms with monsters/items/traps."""
        rng = rng or random
        self.rooms = []

        for _ in range(max_rooms):
            w = rng.randint(room_min_size, room_max_size)
            h = rng.randint(room_min_size, room_max_size)
            if w > self.width - 3 or h > self.height - 3:
                continue  # room too big to fit on this map at all
            x = rng.randint(1, self.width - w - 2)
            y = rng.randint(1, self.height - h - 2)

            new_room = Rect(x, y, w, h)
            if any(new_room.intersect(other) for other in self.rooms):
                continue

            self.create_room(new_room)
            new_x, new_y = new_room.center

            if self.rooms:
                prev_x, prev_y = self.rooms[-1].center
                if rng.randint(0, 1) == 1:
                    self.create_h_tunnel(prev_x, new_x, prev_y)
                    self.create_v_tunnel(prev_y, new_y, new_x)
                else:
                    self.create_v_tunnel(prev_y, new_y, prev_x)
                    self.create_h_tunnel(prev_x, new_x, new_y)
            else:
                player.x, player.y = new_x, new_y

            self.rooms.append(new_room)

        if not self.rooms:
            # Pathological RNG/size combo left no room placed; carve one
            # centered room so the level is always playable.
            fallback = Rect(
                self.width // 2 - 3, self.height // 2 - 3, 6, 6
            )
            self.create_room(fallback)
            player.x, player.y = fallback.center
            self.rooms.append(fallback)

        self.upstairs_pos = self.rooms[0].center
        self.downstairs_pos = self.rooms[-1].center
        return self.rooms

    def walkable_tiles(self):
        for y in range(self.height):
            for x in range(self.width):
                if not self.tiles[y][x].blocked:
                    yield x, y
