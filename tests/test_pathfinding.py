from roguelike.game_map import GameMap
from roguelike.pathfinding import compute_distance_map


def open_map(width=15, height=15):
    gm = GameMap(width, height)
    for row in gm.tiles:
        for tile in row:
            tile.blocked = False
    return gm


def test_origin_distance_zero():
    gm = open_map()
    dmap = compute_distance_map(gm, 7, 7)
    assert dmap[7][7] == 0


def test_adjacent_tiles_including_diagonals_are_distance_one():
    gm = open_map()
    dmap = compute_distance_map(gm, 7, 7)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dx == 0 and dy == 0:
                continue
            assert dmap[7 + dy][7 + dx] == 1


def test_wall_forces_detour():
    gm = open_map()
    for x in range(0, 14):
        gm.tiles[7][x].blocked = True
    gm.tiles[7][13].blocked = False  # leave a gap at the far right

    dmap = compute_distance_map(gm, 0, 6)
    # Straight-line distance would be sqrt(1^2+1^2) ~ 1 step, but the wall
    # forces a long detour around the gap.
    assert dmap[8][0] > 10


def test_unreachable_tile_is_none():
    gm = open_map()
    for x in range(0, 15):
        gm.tiles[7][x].blocked = True  # full wall, no gap
    dmap = compute_distance_map(gm, 0, 0)
    assert dmap[14][14] is None


def test_no_cutting_across_diagonal_wall_corners():
    gm = open_map()
    # Two walls forming a corner; a diagonal step between them should be
    # disallowed even though both endpoints are individually open.
    gm.tiles[5][6].blocked = True
    gm.tiles[6][5].blocked = True
    dmap = compute_distance_map(gm, 5, 5)
    # Unreachable in one diagonal step past the corner, but still reachable
    # by a longer detour since the map is otherwise open.
    assert dmap[6][6] is not None
    assert dmap[6][6] > 1
