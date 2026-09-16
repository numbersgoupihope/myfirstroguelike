"""Populates a freshly-carved GameMap with stairs, monsters, items and traps,
scaling everything by dungeon depth."""

import random

from roguelike import constants, item_data, monster_data
from roguelike.components.stairs import Stairs
from roguelike.components.trap import Trap
from roguelike.entity import Entity, RenderOrder, get_entities_at

MAX_MONSTERS_TABLE = [[2, 1], [3, 4], [4, 6], [5, 8]]
MAX_ITEMS_TABLE = [[1, 1], [2, 4], [3, 7]]

MONSTER_CHANCES = {
    "rat": [[80, 1], [40, 4], [0, 7]],
    "kobold": [[60, 1], [30, 5]],
    "jackal": [[50, 1], [20, 6]],
    "giant_bat": [[40, 1], [15, 6]],
    "fungus": [[25, 1], [10, 6]],
    "goblin": [[35, 2], [55, 4], [20, 8]],
    "goblin_archer": [[20, 3], [30, 6]],
    "cave_spider": [[30, 3], [20, 8]],
    "orc": [[25, 4], [45, 6], [20, 9]],
    "skeleton": [[20, 5], [30, 8]],
    "zombie": [[20, 5], [25, 8]],
    "dark_elf": [[15, 6], [20, 9]],
    "orc_brute": [[15, 6], [25, 9]],
    "troll": [[10, 7], [25, 10]],
    "ogre": [[10, 8], [20, 10]],
    "vampire": [[8, 8], [15, 10]],
    "minotaur": [[5, 9], [15, 10]],
}

ITEM_CHANCES = {
    "healing_potion": [[35, 1]],
    "greater_healing_potion": [[10, 4], [20, 7]],
    "strength_potion": [[10, 3]],
    "antidote_potion": [[12, 2]],
    "poison_potion": [[8, 1], [4, 5]],
    "lightning_scroll": [[15, 3]],
    "fireball_scroll": [[10, 5]],
    "confusion_scroll": [[15, 3]],
    "teleport_scroll": [[10, 4]],
    "mapping_scroll": [[8, 3]],
    "food_ration": [[30, 1]],
    "dagger": [[6, 1]],
    "short_sword": [[8, 2]],
    "sword": [[10, 3]],
    "battle_axe": [[5, 6]],
    "leather_armor": [[10, 1]],
    "chain_mail": [[10, 4]],
    "plate_armor": [[5, 7]],
    "shield": [[10, 2]],
    "tower_shield": [[5, 6]],
    "gold": [[40, 1]],
}

MONSTER_FACTORIES = {
    "rat": monster_data.make_rat,
    "kobold": monster_data.make_kobold,
    "jackal": monster_data.make_jackal,
    "giant_bat": monster_data.make_giant_bat,
    "fungus": monster_data.make_fungus,
    "goblin": monster_data.make_goblin,
    "goblin_archer": monster_data.make_goblin_archer,
    "cave_spider": monster_data.make_cave_spider,
    "orc": monster_data.make_orc,
    "skeleton": monster_data.make_skeleton,
    "zombie": monster_data.make_zombie,
    "dark_elf": monster_data.make_dark_elf,
    "orc_brute": monster_data.make_orc_brute,
    "troll": monster_data.make_troll,
    "ogre": monster_data.make_ogre,
    "vampire": monster_data.make_vampire,
    "minotaur": monster_data.make_minotaur,
}

ITEM_FACTORIES = {
    "healing_potion": item_data.make_healing_potion,
    "greater_healing_potion": item_data.make_greater_healing_potion,
    "strength_potion": item_data.make_strength_potion,
    "antidote_potion": item_data.make_antidote_potion,
    "poison_potion": item_data.make_poison_potion,
    "lightning_scroll": item_data.make_lightning_scroll,
    "fireball_scroll": item_data.make_fireball_scroll,
    "confusion_scroll": item_data.make_confusion_scroll,
    "teleport_scroll": item_data.make_teleport_scroll,
    "mapping_scroll": item_data.make_mapping_scroll,
    "food_ration": item_data.make_food_ration,
    "dagger": item_data.make_dagger,
    "short_sword": item_data.make_short_sword,
    "sword": item_data.make_sword,
    "battle_axe": item_data.make_battle_axe,
    "leather_armor": item_data.make_leather_armor,
    "chain_mail": item_data.make_chain_mail,
    "plate_armor": item_data.make_plate_armor,
    "shield": item_data.make_shield,
    "tower_shield": item_data.make_tower_shield,
}

TRAP_KINDS = ["dart", "pit", "poison_gas", "confusion", "alarm"]


def from_dungeon_level(table, dungeon_level):
    """Pick the value whose min-level threshold is the highest one not
    exceeding ``dungeon_level``. ``table`` entries are ``[value, min_level]``
    and need not be pre-sorted."""
    value = 0
    for entry_value, min_level in sorted(table, key=lambda e: e[1]):
        if min_level <= dungeon_level:
            value = entry_value
        else:
            break
    return value


def random_choice_from_weights(weights, rng):
    choices = [(name, w) for name, w in weights.items() if w > 0]
    if not choices:
        return None
    total = sum(w for _, w in choices)
    roll = rng.uniform(0, total)
    upto = 0.0
    for name, w in choices:
        upto += w
        if roll <= upto:
            return name
    return choices[-1][0]


def make_trap(kind, level, rng):
    if kind == "dart":
        return Trap("dart", damage=rng.randint(2, 4) + level // 2)
    if kind == "pit":
        return Trap("pit", damage=rng.randint(3, 6) + level // 2)
    if kind == "poison_gas":
        return Trap("poison_gas", damage=2, poison_turns=6)
    if kind == "confusion":
        return Trap("confusion", confusion_turns=8)
    return Trap("alarm")


def place_stairs(game_map, entities):
    up_x, up_y = game_map.upstairs_pos
    down_x, down_y = game_map.downstairs_pos

    if game_map.dungeon_level > 1:
        up_name = "Stairs Up"
        up_dest = game_map.dungeon_level - 1
    else:
        up_name = "Stairs to the Surface"
        up_dest = 0

    entities.append(
        Entity(
            up_x,
            up_y,
            "<",
            "stairs",
            up_name,
            render_order=RenderOrder.TRAP,
            stairs=Stairs(up_dest, "up"),
            always_visible=True,
        )
    )
    entities.append(
        Entity(
            down_x,
            down_y,
            ">",
            "stairs",
            "Stairs Down",
            render_order=RenderOrder.TRAP,
            stairs=Stairs(game_map.dungeon_level + 1, "down"),
            always_visible=True,
        )
    )


def place_amulet_and_guardian(game_map, entities, rng):
    room = game_map.rooms[-1]
    x, y = room.center
    entities.append(item_data.make_amulet(x, y))

    gx, gy = x, y
    for _ in range(20):
        cand_x = rng.randint(room.x1 + 1, room.x2 - 1)
        cand_y = rng.randint(room.y1 + 1, room.y2 - 1)
        if (cand_x, cand_y) != (x, y):
            gx, gy = cand_x, cand_y
            break
    entities.append(monster_data.make_dragon(gx, gy))


def populate_dungeon(game_map, entities, rng=None):
    """Fill every room except the starting one with monsters, items and
    traps, weighted by ``game_map.dungeon_level``."""
    rng = rng or random
    level = game_map.dungeon_level

    max_monsters = from_dungeon_level(MAX_MONSTERS_TABLE, level)
    max_items = from_dungeon_level(MAX_ITEMS_TABLE, level)
    monster_weights = {name: from_dungeon_level(table, level) for name, table in MONSTER_CHANCES.items()}
    item_weights = {name: from_dungeon_level(table, level) for name, table in ITEM_CHANCES.items()}
    trap_chance = min(0.6, 0.06 + level * 0.03)

    for room in game_map.rooms[1:]:
        for _ in range(rng.randint(0, max_monsters)):
            x = rng.randint(room.x1 + 1, room.x2 - 1)
            y = rng.randint(room.y1 + 1, room.y2 - 1)
            if get_entities_at(entities, x, y):
                continue
            name = random_choice_from_weights(monster_weights, rng)
            if name:
                entities.append(MONSTER_FACTORIES[name](x, y))

        for _ in range(rng.randint(0, max_items)):
            x = rng.randint(room.x1 + 1, room.x2 - 1)
            y = rng.randint(room.y1 + 1, room.y2 - 1)
            if get_entities_at(entities, x, y):
                continue
            name = random_choice_from_weights(item_weights, rng)
            if name == "gold":
                entities.append(item_data.make_gold(x, y, rng.randint(2, 10) * level))
            elif name:
                entities.append(ITEM_FACTORIES[name](x, y))

        if rng.random() < trap_chance:
            x = rng.randint(room.x1 + 1, room.x2 - 1)
            y = rng.randint(room.y1 + 1, room.y2 - 1)
            occupied = get_entities_at(entities, x, y)
            on_stairs = (x, y) in (game_map.upstairs_pos, game_map.downstairs_pos)
            if not occupied and not on_stairs:
                kind = rng.choice(TRAP_KINDS)
                game_map.tiles[y][x].trap = make_trap(kind, level, rng)

    if level == constants.AMULET_DEPTH:
        place_amulet_and_guardian(game_map, entities, rng)
