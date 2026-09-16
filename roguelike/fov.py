"""Recursive symmetric shadowcasting field-of-view.

A from-scratch implementation of the well-known recursive shadowcasting
algorithm (see Bjorn Bergstrom's original writeup). We octant-transform the
map eight times around the origin so a single recursive scan function
handles all directions.
"""

MULTIPLIERS = [
    (1, 0, 0, -1),
    (0, 1, -1, 0),
    (0, -1, -1, 0),
    (-1, 0, 0, -1),
    (-1, 0, 0, 1),
    (0, -1, 1, 0),
    (0, 1, 1, 0),
    (1, 0, 0, 1),
]


def compute_fov(game_map, origin_x, origin_y, radius):
    """Return a set of (x, y) tiles visible from the origin within radius."""
    visible = {(origin_x, origin_y)}

    for xx, xy, yx, yy in MULTIPLIERS:
        _cast_octant(
            game_map, visible, origin_x, origin_y, radius, 1, 1.0, 0.0, xx, xy, yx, yy
        )

    return visible


def _blocks_sight(game_map, x, y):
    if not game_map.in_bounds(x, y):
        return True
    return game_map.tiles[y][x].block_sight


def _cast_octant(game_map, visible, cx, cy, radius, row, start_slope, end_slope, xx, xy, yx, yy):
    if start_slope < end_slope:
        return

    radius_sq = radius * radius
    next_start_slope = start_slope

    for i in range(row, radius + 1):
        blocked = False
        dy = -i
        for dx in range(-i, 1):
            l_slope = (dx - 0.5) / (dy + 0.5)
            r_slope = (dx + 0.5) / (dy - 0.5)
            if start_slope < r_slope:
                continue
            if end_slope > l_slope:
                break

            map_x = cx + dx * xx + dy * xy
            map_y = cy + dx * yx + dy * yy

            if dx * dx + dy * dy <= radius_sq and game_map.in_bounds(map_x, map_y):
                visible.add((map_x, map_y))

            if blocked:
                if _blocks_sight(game_map, map_x, map_y):
                    next_start_slope = r_slope
                    continue
                else:
                    blocked = False
                    start_slope = next_start_slope
            else:
                if _blocks_sight(game_map, map_x, map_y) and i < radius:
                    blocked = True
                    _cast_octant(
                        game_map,
                        visible,
                        cx,
                        cy,
                        radius,
                        i + 1,
                        start_slope,
                        l_slope,
                        xx,
                        xy,
                        yx,
                        yy,
                    )
                    next_start_slope = r_slope

        if blocked:
            break
