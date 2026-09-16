"""Dijkstra-style "scent" map used for monster chasing.

Rather than run A* per-monster every turn, we flood-fill a single distance
map outward from the player once per turn and let every monster simply walk
downhill. This is the classic roguelike "goal map" trick: cheap, and it
makes monsters path around corners and obstacles correctly instead of just
lurching toward the player's raw coordinates.
"""

from collections import deque


def compute_distance_map(game_map, origin_x, origin_y):
    """BFS flood-fill from (origin_x, origin_y) over unblocked tiles.

    Returns a 2D list the size of the map where each cell holds the number
    of steps from the origin, or ``None`` if unreachable.
    """
    height = game_map.height
    width = game_map.width
    distances = [[None] * width for _ in range(height)]

    if not game_map.in_bounds(origin_x, origin_y):
        return distances

    distances[origin_y][origin_x] = 0
    queue = deque([(origin_x, origin_y)])

    while queue:
        x, y = queue.popleft()
        d = distances[y][x]
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                nx, ny = x + dx, y + dy
                if not (0 <= nx < width and 0 <= ny < height):
                    continue
                if distances[ny][nx] is not None:
                    continue
                if game_map.tiles[ny][nx].blocked:
                    continue
                if dx != 0 and dy != 0:
                    # No cutting across diagonal wall corners.
                    if game_map.tiles[y][nx].blocked and game_map.tiles[ny][x].blocked:
                        continue
                distances[ny][nx] = d + 1
                queue.append((nx, ny))

    return distances
