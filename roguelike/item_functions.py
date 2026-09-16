"""Effect functions bound to items via ``Item(use_function=...)``.

Every function takes the *user* (always the player in practice) as its
first argument, plus keyword arguments that are a merge of the item's own
fixed parameters (baked in at creation time, e.g. ``amount=15``) and
per-call context the engine supplies fresh each turn (``entities``,
``game_map``, ``fov_tiles``, ``target_x``/``target_y``, ``rng``).

Each returns a list of action-result dicts. ``{"consumed": True}`` tells
the inventory to remove the item after use.
"""

import random

from roguelike.entity import get_entities_at
from roguelike.message_log import Message


def heal(user, amount, **kwargs):
    if user.fighter.hp == user.fighter.max_hp:
        return [{"message": Message("You are already at full health.", "msg_info")}]
    user.fighter.heal(amount)
    return [
        {
            "consumed": True,
            "message": Message(
                f"Your wounds start to close. (+{amount} HP)", "msg_good"
            ),
        }
    ]


def gain_strength(user, amount, **kwargs):
    user.fighter.base_power += amount
    return [
        {
            "consumed": True,
            "message": Message(
                f"Raw power surges through you! (+{amount} power, permanently)",
                "msg_good",
            ),
        }
    ]


def cure_status(user, **kwargs):
    cured = False
    if user.status_effects:
        cured = user.status_effects.is_poisoned or user.status_effects.is_confused
        user.status_effects.poison_turns = 0
        user.status_effects.confusion_turns = 0
    if cured:
        message = Message("A cool wave washes over you, purging the poison and fog from your mind.", "msg_good")
    else:
        message = Message("You feel nothing happen.", "msg_info")
    return [{"consumed": True, "message": message}]


def poison_trap_potion(user, damage, poison_turns, **kwargs):
    results = [{"message": Message("The potion was foul -- it was poisoned!", "msg_bad")}]
    if user.status_effects:
        user.status_effects.apply_poison(poison_turns, damage)
    results.append({"consumed": True})
    return results


def eat_food(user, nutrition, **kwargs):
    if user.hunger is None:
        return [{"consumed": True}]
    was_starving = user.hunger.eat(nutrition)
    message = "That food really hit the spot." if not was_starving else "The food saves you from starvation!"
    return [{"consumed": True, "message": Message(message, "msg_good")}]


def cast_lightning(user, entities, fov_tiles, damage, max_range, **kwargs):
    target = None
    closest_distance = max_range + 1

    for entity in entities:
        if entity is user or entity.fighter is None:
            continue
        if (entity.x, entity.y) not in fov_tiles:
            continue
        distance = user.distance_to(entity)
        if distance < closest_distance:
            target = entity
            closest_distance = distance

    if target is None:
        return [{"message": Message("No enemy is close enough to strike.", "msg_info")}]

    results = [
        {
            "consumed": True,
            "message": Message(
                f"A lightning bolt crashes into the {target.name} for {damage} damage!",
                "msg_crit",
            ),
        }
    ]
    results.extend(target.fighter.take_damage(damage))
    return results


def cast_fireball(user, entities, target_x, target_y, radius, damage, fov_tiles=None, **kwargs):
    if fov_tiles is not None and (target_x, target_y) not in fov_tiles:
        return [{"message": Message("You cannot target a tile you can't see.", "msg_warning")}]

    results = [
        {
            "consumed": True,
            "message": Message(
                f"The scroll erupts in flame, roasting everything within {radius} tiles!",
                "msg_crit",
            ),
        }
    ]
    for entity in entities:
        if entity.fighter is not None and entity.distance(target_x, target_y) <= radius:
            color = "msg_bad" if entity is user else "msg_warning"
            results.append(
                {
                    "message": Message(
                        f"The {entity.name} is engulfed in flame for {damage} damage!",
                        color,
                    )
                }
            )
            results.extend(entity.fighter.take_damage(damage))
    return results


def cast_confuse(user, entities, target_x, target_y, turns, fov_tiles=None, **kwargs):
    if fov_tiles is not None and (target_x, target_y) not in fov_tiles:
        return [{"message": Message("You cannot target a tile you can't see.", "msg_warning")}]

    target = next(
        (e for e in get_entities_at(entities, target_x, target_y) if e.ai is not None),
        None,
    )
    if target is None:
        return [{"message": Message("There is nothing there to confuse.", "msg_info")}]

    if target.status_effects:
        target.status_effects.apply_confusion(turns)
    return [
        {
            "consumed": True,
            "message": Message(
                f"The eyes of the {target.name} glaze over as it stumbles around!",
                "msg_good",
            ),
        }
    ]


def scroll_teleport(user, game_map, entities, rng=None, **kwargs):
    rng = rng or random
    from roguelike.entity import get_blocking_entity

    candidates = [
        (x, y)
        for x, y in game_map.walkable_tiles()
        if get_blocking_entity(entities, x, y) is None
    ]
    if not candidates:
        return [{"message": Message("The scroll fizzles uselessly.", "msg_info")}]

    user.x, user.y = rng.choice(candidates)
    return [
        {
            "consumed": True,
            "message": Message("You are wrenched through space in a flash of light!", "msg_good"),
        }
    ]


def scroll_magic_mapping(user, game_map, **kwargs):
    for row in game_map.tiles:
        for tile in row:
            tile.explored = True
    return [
        {
            "consumed": True,
            "message": Message("The layout of the level is revealed to you.", "msg_good"),
        }
    ]
