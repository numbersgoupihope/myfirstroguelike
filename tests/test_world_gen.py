import random

from roguelike import constants, world_gen
from roguelike.entity import Entity
from roguelike.game_map import GameMap


def test_from_dungeon_level_picks_highest_applicable_threshold():
    table = [[10, 1], [20, 3], [30, 6]]
    assert world_gen.from_dungeon_level(table, 1) == 10
    assert world_gen.from_dungeon_level(table, 2) == 10
    assert world_gen.from_dungeon_level(table, 3) == 20
    assert world_gen.from_dungeon_level(table, 5) == 20
    assert world_gen.from_dungeon_level(table, 6) == 30
    assert world_gen.from_dungeon_level(table, 100) == 30


def test_from_dungeon_level_zero_before_first_threshold():
    table = [[10, 5]]
    assert world_gen.from_dungeon_level(table, 1) == 0


def test_from_dungeon_level_unsorted_input_still_works():
    table = [[30, 6], [10, 1], [20, 3]]
    assert world_gen.from_dungeon_level(table, 4) == 20


def test_random_choice_from_weights_only_returns_nonzero_entries():
    rng = random.Random(1)
    weights = {"a": 0, "b": 0, "c": 5}
    for _ in range(50):
        assert world_gen.random_choice_from_weights(weights, rng) == "c"


def test_random_choice_from_weights_all_zero_returns_none():
    rng = random.Random(1)
    assert world_gen.random_choice_from_weights({"a": 0, "b": 0}, rng) is None


def test_random_choice_from_weights_distribution_roughly_matches_weights():
    rng = random.Random(42)
    weights = {"common": 90, "rare": 10}
    counts = {"common": 0, "rare": 0}
    for _ in range(2000):
        counts[world_gen.random_choice_from_weights(weights, rng)] += 1
    ratio = counts["common"] / (counts["common"] + counts["rare"])
    assert 0.8 < ratio < 0.97


def _generate_level(level, rng):
    player = Entity(0, 0, "@", "player", "you")
    gm = GameMap(constants.MAP_WIDTH, constants.MAP_HEIGHT, level)
    gm.make_map(constants.MAX_ROOMS, constants.ROOM_MIN_SIZE, constants.ROOM_MAX_SIZE, player, rng=rng)
    entities = [player]
    world_gen.place_stairs(gm, entities)
    world_gen.populate_dungeon(gm, entities, rng=rng)
    return gm, entities, player


def test_starting_room_has_no_monsters_or_items():
    rng = random.Random(3)
    gm, entities, player = _generate_level(5, rng)
    start_room = gm.rooms[0]
    for entity in entities:
        if entity is player or entity.stairs is not None:
            continue
        in_start_room = (
            start_room.x1 < entity.x < start_room.x2 and start_room.y1 < entity.y < start_room.y2
        )
        assert not in_start_room, f"{entity.name} spawned in the starting room"


def test_stairs_up_and_down_both_placed():
    rng = random.Random(4)
    gm, entities, player = _generate_level(3, rng)
    directions = {e.stairs.direction for e in entities if e.stairs}
    assert directions == {"up", "down"}


def test_level_one_upstairs_leads_to_surface():
    rng = random.Random(4)
    gm, entities, player = _generate_level(1, rng)
    up = next(e for e in entities if e.stairs and e.stairs.direction == "up")
    assert up.stairs.floor == 0


def test_amulet_and_dragon_placed_at_amulet_depth():
    rng = random.Random(9)
    gm, entities, player = _generate_level(constants.AMULET_DEPTH, rng)
    assert any(e.name == "Amulet of Yendor" for e in entities)
    assert any(e.name == "ancient dragon" for e in entities)


def test_no_amulet_before_amulet_depth():
    rng = random.Random(9)
    gm, entities, player = _generate_level(constants.AMULET_DEPTH - 1, rng)
    assert not any(e.name == "Amulet of Yendor" for e in entities)


def test_traps_never_placed_on_stairs():
    for seed in range(10):
        rng = random.Random(seed)
        gm, entities, player = _generate_level(6, rng)
        for row in gm.tiles:
            for tile in row:
                if tile.trap is None:
                    continue
        # Re-derive positions directly to check trap tiles vs stairs tiles.
        trap_positions = {
            (x, y)
            for y, row in enumerate(gm.tiles)
            for x, tile in enumerate(row)
            if tile.trap is not None
        }
        assert gm.upstairs_pos not in trap_positions
        assert gm.downstairs_pos not in trap_positions
