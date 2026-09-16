"""The generic game object: player, monsters, items, stairs all share this
one class and are differentiated by which components are attached."""

import math
from enum import IntEnum


class RenderOrder(IntEnum):
    CORPSE = 1
    TRAP = 2
    ITEM = 3
    ACTOR = 4
    PLAYER = 5


class Entity:
    """A generic object: the player, a monster, an item, stairs, ...

    Behaviour is added via optional "components" (fighter, ai, item,
    inventory, stairs, level, equipment, equippable). Each component that
    is provided gets an ``owner`` back-reference set to this entity so it
    can call back into the world (e.g. a Fighter dealing damage needs to
    know its own position for death messages).
    """

    def __init__(
        self,
        x,
        y,
        char,
        color,
        name,
        blocks=False,
        render_order=RenderOrder.CORPSE,
        fighter=None,
        ai=None,
        item=None,
        inventory=None,
        stairs=None,
        level=None,
        equipment=None,
        equippable=None,
        trap=None,
        status_effects=None,
        hunger=None,
        always_visible=False,
    ):
        self.x = x
        self.y = y
        self.char = char
        self.color = color
        self.name = name
        self.blocks = blocks
        self.render_order = render_order
        self.always_visible = always_visible

        self.fighter = fighter
        self.ai = ai
        self.item = item
        self.inventory = inventory
        self.stairs = stairs
        self.level = level
        self.equipment = equipment
        self.equippable = equippable
        self.trap = trap
        self.status_effects = status_effects
        self.hunger = hunger

        for component in (
            fighter,
            ai,
            item,
            inventory,
            stairs,
            level,
            equipment,
            trap,
            status_effects,
            hunger,
        ):
            if component is not None:
                component.owner = self

        # An Equippable makes an Item usable/wearable; make sure the item
        # component exists so it can live in an inventory.
        if equippable is not None:
            equippable.owner = self
            if item is None:
                from roguelike.components.item import Item

                self.item = Item()
                self.item.owner = self

    def move(self, dx, dy):
        self.x += dx
        self.y += dy

    def distance_to(self, other):
        return self.distance(other.x, other.y)

    def distance(self, x, y):
        return math.sqrt((x - self.x) ** 2 + (y - self.y) ** 2)

    def move_towards_distance_map(self, distance_map, game_map, entities):
        """Step one tile in the direction of decreasing distance value.

        ``distance_map`` is a 2D array of ints/``None`` as produced by
        :mod:`roguelike.pathfinding`. Falls back to doing nothing if no
        improving, unblocked neighbour exists (e.g. the monster is boxed
        in by other monsters).
        """
        best = None
        best_score = distance_map[self.y][self.x]
        if best_score is None:
            return False

        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                nx, ny = self.x + dx, self.y + dy
                if not game_map.in_bounds(nx, ny):
                    continue
                if game_map.tiles[ny][nx].blocked:
                    continue
                # Disallow cutting across a diagonal formed by two walls.
                if dx != 0 and dy != 0:
                    if game_map.tiles[self.y][nx].blocked and game_map.tiles[ny][self.x].blocked:
                        continue
                score = distance_map[ny][nx]
                if score is None:
                    continue
                if get_blocking_entity(entities, nx, ny) is not None:
                    continue
                if score < best_score:
                    best_score = score
                    best = (dx, dy)

        if best:
            self.move(*best)
            return True
        return False

    def move_towards_point(self, target_x, target_y, game_map, entities):
        """Greedy line-of-sight movement (used when no distance map is
        available, e.g. for entities acting outside the player's turn
        cadence)."""
        dx = target_x - self.x
        dy = target_y - self.y
        distance = math.sqrt(dx**2 + dy**2)
        if distance == 0:
            return
        dx = int(round(dx / distance))
        dy = int(round(dy / distance))
        nx, ny = self.x + dx, self.y + dy
        if (
            game_map.in_bounds(nx, ny)
            and not game_map.tiles[ny][nx].blocked
            and get_blocking_entity(entities, nx, ny) is None
        ):
            self.move(dx, dy)

    def move_away_from(self, from_x, from_y, game_map, entities):
        dx = self.x - from_x
        dy = self.y - from_y
        distance = math.sqrt(dx**2 + dy**2)
        if distance == 0:
            dx, dy = 1, 0
        else:
            dx = int(round(dx / distance))
            dy = int(round(dy / distance))
        nx, ny = self.x + dx, self.y + dy
        if (
            game_map.in_bounds(nx, ny)
            and not game_map.tiles[ny][nx].blocked
            and get_blocking_entity(entities, nx, ny) is None
        ):
            self.move(dx, dy)
            return True
        return False


def get_blocking_entity(entities, x, y):
    for entity in entities:
        if entity.blocks and entity.x == x and entity.y == y:
            return entity
    return None


def get_entities_at(entities, x, y):
    return [e for e in entities if e.x == x and e.y == y]
