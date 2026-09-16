"""Monster behaviours. Each AI is given the player-centred distance map for
the current turn (see :mod:`roguelike.pathfinding`) plus the set of tiles
currently visible to the player, which we reuse (reciprocally) as "tiles the
monster can see the player from"."""

import random


def _random_step(rng):
    rng = rng or random
    return rng.choice([(-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)])


def _stumble(monster, game_map, entities, rng):
    from roguelike.message_log import Message

    dx, dy = _random_step(rng)
    nx, ny = monster.x + dx, monster.y + dy
    results = [
        {"message": Message(f"The {monster.name} stumbles around in confusion.", "msg_info")}
    ]
    if game_map.in_bounds(nx, ny) and not game_map.tiles[ny][nx].blocked:
        from roguelike.entity import get_blocking_entity

        if get_blocking_entity(entities, nx, ny) is None:
            monster.move(dx, dy)
    return results


class BasicMonster:
    """Chases the player when it can see them, attacks when adjacent."""

    def __init__(self, chase_range=999):
        self.chase_range = chase_range
        self.owner = None

    def take_turn(self, target, visible_to_player, game_map, entities, distance_map, rng=None):
        monster = self.owner
        results = []

        if monster.status_effects and monster.status_effects.is_confused:
            return _stumble(monster, game_map, entities, rng)

        if (monster.x, monster.y) not in visible_to_player:
            return results

        distance = monster.distance_to(target)
        if distance >= 2:
            if distance_map is not None:
                monster.move_towards_distance_map(distance_map, game_map, entities)
        elif target.fighter and target.fighter.hp > 0:
            results.extend(monster.fighter.attack(target, rng=rng))

        return results


class StationaryMonster:
    """Never moves; only attacks when the player wanders adjacent. Good for
    ambush-y dungeon flora like molds and fungi."""

    def __init__(self):
        self.owner = None

    def take_turn(self, target, visible_to_player, game_map, entities, distance_map, rng=None):
        monster = self.owner
        results = []
        if monster.status_effects and monster.status_effects.is_confused:
            return results
        if monster.distance_to(target) < 1.5 and target.fighter and target.fighter.hp > 0:
            results.extend(monster.fighter.attack(target, rng=rng))
        return results


class RangedMonster:
    """Keeps its distance and takes potshots; retreats if the player closes
    in, chases if the player is out of range entirely."""

    def __init__(self, preferred_range=4, min_range=2):
        self.preferred_range = preferred_range
        self.min_range = min_range
        self.owner = None

    def take_turn(self, target, visible_to_player, game_map, entities, distance_map, rng=None):
        monster = self.owner
        results = []

        if monster.status_effects and monster.status_effects.is_confused:
            return _stumble(monster, game_map, entities, rng)

        if (monster.x, monster.y) not in visible_to_player:
            return results

        distance = monster.distance_to(target)

        if distance <= self.min_range:
            monster.move_away_from(target.x, target.y, game_map, entities)
        elif distance <= self.preferred_range:
            if target.fighter and target.fighter.hp > 0:
                results.extend(monster.fighter.attack(target, rng=rng))
        else:
            if distance_map is not None:
                monster.move_towards_distance_map(distance_map, game_map, entities)

        return results
