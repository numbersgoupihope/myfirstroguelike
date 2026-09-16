from roguelike.fov import compute_fov
from roguelike.game_map import GameMap


def open_map(width=21, height=21):
    gm = GameMap(width, height)
    for row in gm.tiles:
        for tile in row:
            tile.blocked = False
            tile.block_sight = False
    return gm


def test_origin_always_visible():
    gm = open_map()
    visible = compute_fov(gm, 10, 10, 5)
    assert (10, 10) in visible


def test_open_room_visible_within_radius():
    gm = open_map()
    radius = 5
    visible = compute_fov(gm, 10, 10, radius)
    # Every tile within the radius on an open map should be visible.
    for dx in range(-radius, radius + 1):
        for dy in range(-radius, radius + 1):
            if dx * dx + dy * dy <= radius * radius:
                assert (10 + dx, 10 + dy) in visible


def test_beyond_radius_not_visible():
    gm = open_map()
    visible = compute_fov(gm, 10, 10, 3)
    assert (10, 15) not in visible
    assert (17, 10) not in visible


def test_wall_blocks_line_of_sight():
    gm = open_map()
    # A solid wall segment directly below the origin should shadow tiles
    # further below it.
    for x in range(5, 16):
        gm.tiles[12][x].blocked = True
        gm.tiles[12][x].block_sight = True

    visible = compute_fov(gm, 10, 10, 8)
    # The wall itself is visible (you can see the wall)...
    assert (10, 12) in visible
    # ...but straight past it, directly behind the wall, should not be.
    assert (10, 15) not in visible


def test_fov_does_not_leak_around_corner():
    gm = open_map()
    # Build an "L" wall enclosing everything except a thin corridor so we
    # can check that vision doesn't magically bend around solid corners.
    for y in range(0, 21):
        gm.tiles[y][10].blocked = True
        gm.tiles[y][10].block_sight = True
    gm.tiles[10][10].blocked = False
    gm.tiles[10][10].block_sight = False

    visible = compute_fov(gm, 5, 10, 10)
    # Directly across through the gap should be visible.
    assert (10, 10) in visible
    # Far to the other side of the wall, away from the gap's row, should
    # not be reachable by sight.
    assert (15, 0) not in visible
