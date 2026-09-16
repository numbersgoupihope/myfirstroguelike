import random

from roguelike import item_functions as ifn
from roguelike.components.fighter import Fighter
from roguelike.components.hunger import Hunger
from roguelike.components.status_effects import StatusEffects
from roguelike.entity import Entity
from roguelike.game_map import GameMap


def make_actor(name, x=0, y=0, hp=20, defense=0, power=3, **kwargs):
    return Entity(
        x,
        y,
        "x",
        "default",
        name,
        blocks=True,
        fighter=Fighter(hp=hp, defense=defense, power=power),
        status_effects=StatusEffects(),
        **kwargs,
    )


def test_heal_restores_hp_and_consumes():
    user = make_actor("you", hp=20)
    user.fighter.hp = 5
    results = ifn.heal(user, amount=10)
    assert user.fighter.hp == 15
    assert results[0]["consumed"] is True


def test_heal_at_full_hp_is_not_consumed():
    user = make_actor("you", hp=20)
    results = ifn.heal(user, amount=10)
    assert user.fighter.hp == 20
    assert not any(r.get("consumed") for r in results)


def test_gain_strength_is_permanent():
    user = make_actor("you", power=4)
    ifn.gain_strength(user, amount=2)
    assert user.fighter.base_power == 6


def test_cure_status_clears_poison_and_confusion():
    user = make_actor("you")
    user.status_effects.apply_poison(5, 3)
    user.status_effects.apply_confusion(5)
    ifn.cure_status(user)
    assert not user.status_effects.is_poisoned
    assert not user.status_effects.is_confused


def test_eat_food_refills_hunger():
    user = make_actor("you", hunger=Hunger(max_value=1000))
    user.hunger.current = 100
    ifn.eat_food(user, nutrition=500)
    assert user.hunger.current == 600


def test_cast_lightning_hits_nearest_visible_enemy():
    user = make_actor("you", x=0, y=0, power=5)
    far = make_actor("far orc", x=5, y=0, hp=30)
    near = make_actor("near orc", x=1, y=0, hp=30)
    entities = [user, far, near]
    fov_tiles = {(0, 0), (1, 0), (5, 0)}

    ifn.cast_lightning(user, entities=entities, fov_tiles=fov_tiles, damage=10, max_range=10)
    assert near.fighter.hp == 20
    assert far.fighter.hp == 30


def test_cast_lightning_no_target_in_range():
    user = make_actor("you", x=0, y=0)
    entities = [user]
    results = ifn.cast_lightning(user, entities=entities, fov_tiles=set(), damage=10, max_range=5)
    assert not any(r.get("consumed") for r in results)


def test_cast_fireball_hits_everyone_in_radius_including_self():
    user = make_actor("you", x=5, y=5, hp=30)
    ally_like_monster = make_actor("orc", x=6, y=5, hp=30)
    far_away = make_actor("goblin", x=20, y=20, hp=30)
    entities = [user, ally_like_monster, far_away]
    fov_tiles = {(5, 5)}

    ifn.cast_fireball(user, entities=entities, target_x=5, target_y=5, radius=2, damage=8, fov_tiles=fov_tiles)
    assert user.fighter.hp == 22
    assert ally_like_monster.fighter.hp == 22
    assert far_away.fighter.hp == 30


def test_cast_fireball_rejects_target_outside_fov():
    user = make_actor("you", x=0, y=0)
    results = ifn.cast_fireball(
        user, entities=[user], target_x=5, target_y=5, radius=2, damage=8, fov_tiles={(0, 0)}
    )
    assert not any(r.get("consumed") for r in results)


def test_cast_confuse_applies_status_to_targeted_monster():
    user = make_actor("you", x=0, y=0)
    monster = make_actor("goblin", x=1, y=0)
    monster.ai = object()  # cast_confuse only targets entities with an ai
    entities = [user, monster]
    fov_tiles = {(1, 0)}

    ifn.cast_confuse(user, entities=entities, target_x=1, target_y=0, turns=6, fov_tiles=fov_tiles)
    assert monster.status_effects.confusion_turns == 6


def test_cast_confuse_no_target_present():
    user = make_actor("you", x=0, y=0)
    results = ifn.cast_confuse(user, entities=[user], target_x=1, target_y=0, turns=6, fov_tiles={(1, 0)})
    assert not any(r.get("consumed") for r in results)


def test_scroll_teleport_moves_to_walkable_tile():
    gm = GameMap(10, 10)
    for row in gm.tiles:
        for tile in row:
            tile.blocked = False
    user = make_actor("you", x=0, y=0)
    ifn.scroll_teleport(user, game_map=gm, entities=[user], rng=random.Random(1))
    assert gm.in_bounds(user.x, user.y)
    assert not gm.tiles[user.y][user.x].blocked


def test_scroll_magic_mapping_reveals_all_tiles():
    gm = GameMap(5, 5)
    user = make_actor("you")
    ifn.scroll_magic_mapping(user, game_map=gm)
    assert all(tile.explored for row in gm.tiles for tile in row)
