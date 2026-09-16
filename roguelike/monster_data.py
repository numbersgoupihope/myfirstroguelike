"""Factory functions that build monster entities, weakest to strongest."""

from roguelike.components.ai import BasicMonster, RangedMonster, StationaryMonster
from roguelike.components.fighter import Fighter
from roguelike.components.status_effects import StatusEffects
from roguelike.entity import Entity, RenderOrder
from roguelike.message_log import Message


def _poison_bite(attacker, target, damage):
    if not target.status_effects:
        return []
    target.status_effects.apply_poison(4, 2)
    return [{"message": Message(f"The bite of the {attacker.name} festers with poison!", "msg_bad")}]


def _lifesteal(attacker, target, damage):
    if not attacker.fighter:
        return []
    healed = min(damage // 2, attacker.fighter.max_hp - attacker.fighter.hp)
    if healed <= 0:
        return []
    attacker.fighter.heal(healed)
    return [{"message": Message(f"The {attacker.name} drains your vitality!", "msg_bad")}]


def _make(x, y, char, color, name, hp, defense, power, xp, ai, on_hit=None):
    return Entity(
        x,
        y,
        char,
        color,
        name,
        blocks=True,
        render_order=RenderOrder.ACTOR,
        fighter=Fighter(hp=hp, defense=defense, power=power, xp=xp, on_hit=on_hit),
        ai=ai,
        status_effects=StatusEffects(),
    )


def make_rat(x, y):
    return _make(x, y, "r", "monster_weak", "giant rat", 4, 0, 2, 5, BasicMonster())


def make_kobold(x, y):
    return _make(x, y, "k", "monster_weak", "kobold", 6, 0, 3, 8, BasicMonster())


def make_jackal(x, y):
    return _make(x, y, "j", "monster_weak", "jackal", 7, 0, 3, 9, BasicMonster())


def make_giant_bat(x, y):
    return _make(x, y, "b", "monster_weak", "giant bat", 6, 0, 3, 8, BasicMonster())


def make_fungus(x, y):
    return _make(x, y, "F", "monster_weak", "yellow fungus", 10, 1, 2, 10, StationaryMonster())


def make_goblin(x, y):
    return _make(x, y, "g", "monster_normal", "goblin", 10, 1, 3, 12, BasicMonster())


def make_goblin_archer(x, y):
    return _make(x, y, "g", "monster_normal", "goblin archer", 8, 0, 3, 15, RangedMonster(preferred_range=4, min_range=2))


def make_cave_spider(x, y):
    return _make(x, y, "s", "monster_normal", "cave spider", 11, 1, 3, 16, BasicMonster(), on_hit=_poison_bite)


def make_orc(x, y):
    return _make(x, y, "o", "monster_normal", "orc", 16, 2, 5, 25, BasicMonster())


def make_skeleton(x, y):
    return _make(x, y, "z", "monster_normal", "skeleton warrior", 15, 3, 4, 22, BasicMonster())


def make_zombie(x, y):
    return _make(x, y, "Z", "monster_tough", "shambling zombie", 22, 1, 5, 28, BasicMonster())


def make_dark_elf(x, y):
    return _make(x, y, "e", "monster_tough", "dark elf archer", 16, 2, 6, 40, RangedMonster(preferred_range=5, min_range=2))


def make_orc_brute(x, y):
    return _make(x, y, "O", "monster_tough", "orc brute", 24, 2, 7, 38, BasicMonster())


def make_troll(x, y):
    return _make(x, y, "T", "monster_tough", "cave troll", 40, 4, 9, 60, BasicMonster())


def make_ogre(x, y):
    return _make(x, y, "H", "monster_tough", "ogre", 50, 3, 10, 70, BasicMonster())


def make_vampire(x, y):
    return _make(x, y, "V", "monster_boss", "vampire", 38, 3, 9, 65, BasicMonster(), on_hit=_lifesteal)


def make_minotaur(x, y):
    return _make(x, y, "M", "monster_boss", "minotaur", 48, 3, 11, 75, BasicMonster())


def make_dragon(x, y):
    return _make(
        x,
        y,
        "D",
        "monster_boss",
        "ancient dragon",
        90,
        6,
        15,
        250,
        RangedMonster(preferred_range=6, min_range=0),
    )
