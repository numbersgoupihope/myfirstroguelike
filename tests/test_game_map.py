import random
from collections import deque

from roguelike.entity import Entity
from roguelike.game_map import GameMap


def _bfs_reachable(gm, start):
    seen = {start}
    queue = deque([start])
    while queue:
        x, y = queue.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if not gm.in_bounds(nx, ny) or (nx, ny) in seen:
                continue
            if gm.tiles[ny][nx].blocked:
                continue
            seen.add((nx, ny))
            queue.append((nx, ny))
    return seen


def test_make_map_places_player_on_open_tile():
    player = Entity(0, 0, "@", "player", "you")
    gm = GameMap(60, 30)
    gm.make_map(20, 5, 10, player, rng=random.Random(1))
    assert not gm.tiles[player.y][player.x].blocked


def test_all_rooms_reachable_from_player_across_many_seeds():
    for seed in range(25):
        player = Entity(0, 0, "@", "player", "you")
        gm = GameMap(60, 20)
        gm.make_map(30, 4, 8, player, rng=random.Random(seed))
        reachable = _bfs_reachable(gm, (player.x, player.y))
        for room in gm.rooms:
            assert room.center in reachable, f"seed {seed}: room {room.center} unreachable"


def test_rooms_do_not_overlap():
    player = Entity(0, 0, "@", "player", "you")
    gm = GameMap(60, 30)
    gm.make_map(30, 4, 8, player, rng=random.Random(7))
    for i, a in enumerate(gm.rooms):
        for b in gm.rooms[i + 1 :]:
            assert not a.intersect(b)


def test_stairs_positions_are_room_centers():
    player = Entity(0, 0, "@", "player", "you")
    gm = GameMap(60, 20)
    gm.make_map(30, 4, 8, player, rng=random.Random(3))
    assert gm.upstairs_pos == gm.rooms[0].center
    assert gm.downstairs_pos == gm.rooms[-1].center


def test_fallback_room_when_no_room_fits():
    # Room sizes bigger than the map guarantee zero placements, exercising
    # the fallback-room path.
    player = Entity(0, 0, "@", "player", "you")
    gm = GameMap(10, 10)
    gm.make_map(5, 20, 25, player, rng=random.Random(1))
    assert len(gm.rooms) == 1
    assert not gm.tiles[player.y][player.x].blocked
