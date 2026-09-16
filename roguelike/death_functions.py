"""Turns a defeated fighter into an inert corpse (or ends the game, for the
player)."""

from roguelike.entity import RenderOrder
from roguelike.message_log import Message


def kill_monster(monster):
    death_message = Message(f"The {monster.name} is dead!", "msg_good")

    monster.char = "%"
    monster.color = "default"
    monster.blocks = False
    monster.fighter = None
    monster.ai = None
    monster.status_effects = None
    monster.render_order = RenderOrder.CORPSE
    monster.name = f"remains of {monster.name}"

    return [{"message": death_message}]


def kill_player(player):
    player.char = "%"
    player.color = "msg_bad"
    return [{"message": Message("You have died.", "msg_crit")}]
