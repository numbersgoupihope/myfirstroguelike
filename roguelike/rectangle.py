"""Axis-aligned rectangle helper used for room placement."""


class Rect:
    def __init__(self, x, y, w, h):
        self.x1 = x
        self.y1 = y
        self.x2 = x + w
        self.y2 = y + h

    @property
    def center(self):
        center_x = (self.x1 + self.x2) // 2
        center_y = (self.y1 + self.y2) // 2
        return center_x, center_y

    def intersect(self, other):
        """Returns True if this rectangle overlaps with another one (with
        a one-tile buffer so rooms never touch and merge into each other).
        """
        return (
            self.x1 - 1 <= other.x2
            and self.x2 + 1 >= other.x1
            and self.y1 - 1 <= other.y2
            and self.y2 + 1 >= other.y1
        )
