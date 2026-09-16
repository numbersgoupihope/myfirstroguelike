"""Pure, seedable combat math kept separate from the Fighter component so it
can be unit tested without constructing entities."""

import random


def clamp(value, lo, hi):
    return max(lo, min(hi, value))


def hit_chance(power, defense):
    """Chance in [0.05, 0.95] that an attack connects."""
    return clamp(0.75 + 0.03 * (power - defense), 0.05, 0.95)


def roll_attack(power, defense, rng=None):
    """Resolve one attack.

    Returns ``(damage, hit)``. Damage is always >= 1 on a hit and 0 on a
    miss. ``rng`` defaults to the module-level :mod:`random` instance but
    accepts a seeded ``random.Random`` for deterministic tests.
    """
    rng = rng or random

    if rng.random() > hit_chance(power, defense):
        return 0, False

    base = max(1, power - defense // 2)
    variance = rng.randint(0, max(1, power // 3))
    mitigation = rng.randint(0, max(1, defense // 3))
    damage = max(1, base + variance - mitigation)
    return damage, True
