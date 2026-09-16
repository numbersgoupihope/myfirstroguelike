from roguelike import death_functions
from roguelike.components.ai import BasicMonster
from roguelike.components.fighter import Fighter
from roguelike.components.status_effects import StatusEffects
from roguelike.entity import Entity, RenderOrder


def test_kill_monster_converts_to_inert_corpse():
    monster = Entity(
        0,
        0,
        "o",
        "monster_normal",
        "orc",
        blocks=True,
        render_order=RenderOrder.ACTOR,
        fighter=Fighter(hp=0, defense=1, power=1, xp=25),
        ai=BasicMonster(),
        status_effects=StatusEffects(),
    )

    results = death_functions.kill_monster(monster)

    assert monster.fighter is None
    assert monster.ai is None
    assert monster.status_effects is None
    assert monster.blocks is False
    assert monster.char == "%"
    assert monster.render_order == RenderOrder.CORPSE
    assert "remains of orc" == monster.name
    assert any(r.get("message") for r in results)


def test_kill_player_reports_death_message():
    player = Entity(0, 0, "@", "player", "you", fighter=Fighter(hp=0, defense=1, power=1))
    results = death_functions.kill_player(player)
    assert player.char == "%"
    assert any("died" in r["message"].text.lower() for r in results if r.get("message"))
