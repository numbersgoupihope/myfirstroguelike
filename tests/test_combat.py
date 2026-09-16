import random

from roguelike.combat import hit_chance, roll_attack


def test_hit_chance_is_clamped():
    assert hit_chance(power=100, defense=0) <= 0.95
    assert hit_chance(power=0, defense=100) >= 0.05


def test_damage_always_positive_on_hit():
    rng = random.Random(1234)
    for _ in range(2000):
        damage, hit = roll_attack(power=8, defense=3, rng=rng)
        if hit:
            assert damage >= 1
        else:
            assert damage == 0


def test_deterministic_with_seeded_rng():
    a = roll_attack(power=6, defense=2, rng=random.Random(99))
    b = roll_attack(power=6, defense=2, rng=random.Random(99))
    assert a == b


def test_overwhelming_power_wins_most_of_the_time():
    rng = random.Random(5)
    hits = sum(1 for _ in range(500) if roll_attack(power=50, defense=1, rng=rng)[1])
    assert hits > 400


def test_overwhelming_defense_dodges_most_of_the_time():
    rng = random.Random(5)
    hits = sum(1 for _ in range(500) if roll_attack(power=1, defense=50, rng=rng)[1])
    assert hits < 100
