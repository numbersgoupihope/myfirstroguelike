"""Factory functions that build item entities."""

from roguelike import item_functions as ifn
from roguelike.components.equippable import Equippable, EquipmentSlots
from roguelike.components.item import Item
from roguelike.entity import Entity, RenderOrder
from roguelike.message_log import Message


def make_healing_potion(x, y):
    item = Item(use_function=ifn.heal, amount=15)
    return Entity(x, y, "!", "item_potion", "Potion of Healing", item=item, render_order=RenderOrder.ITEM)


def make_greater_healing_potion(x, y):
    item = Item(use_function=ifn.heal, amount=35)
    return Entity(x, y, "!", "item_potion", "Potion of Greater Healing", item=item, render_order=RenderOrder.ITEM)


def make_strength_potion(x, y):
    item = Item(use_function=ifn.gain_strength, amount=1)
    return Entity(x, y, "!", "item_potion", "Potion of Strength", item=item, render_order=RenderOrder.ITEM)


def make_antidote_potion(x, y):
    item = Item(use_function=ifn.cure_status)
    return Entity(x, y, "!", "item_potion", "Potion of Cleansing", item=item, render_order=RenderOrder.ITEM)


def make_poison_potion(x, y):
    item = Item(use_function=ifn.poison_trap_potion, damage=3, poison_turns=6)
    return Entity(x, y, "!", "item_potion", "Potion of Sickness", item=item, render_order=RenderOrder.ITEM)


def make_lightning_scroll(x, y):
    item = Item(use_function=ifn.cast_lightning, damage=28, max_range=6)
    return Entity(x, y, "?", "item_scroll", "Scroll of Lightning Bolt", item=item, render_order=RenderOrder.ITEM)


def make_fireball_scroll(x, y):
    item = Item(
        use_function=ifn.cast_fireball,
        targeting=True,
        targeting_message=Message("Choose a target tile for the fireball.", "msg_info"),
        damage=20,
        radius=3,
    )
    return Entity(x, y, "?", "item_scroll", "Scroll of Fireball", item=item, render_order=RenderOrder.ITEM)


def make_confusion_scroll(x, y):
    item = Item(
        use_function=ifn.cast_confuse,
        targeting=True,
        targeting_message=Message("Choose an enemy to confuse.", "msg_info"),
        turns=10,
    )
    return Entity(x, y, "?", "item_scroll", "Scroll of Confusion", item=item, render_order=RenderOrder.ITEM)


def make_teleport_scroll(x, y):
    item = Item(use_function=ifn.scroll_teleport)
    return Entity(x, y, "?", "item_scroll", "Scroll of Teleportation", item=item, render_order=RenderOrder.ITEM)


def make_mapping_scroll(x, y):
    item = Item(use_function=ifn.scroll_magic_mapping)
    return Entity(x, y, "?", "item_scroll", "Scroll of Magic Mapping", item=item, render_order=RenderOrder.ITEM)


def make_food_ration(x, y):
    item = Item(use_function=ifn.eat_food, nutrition=500)
    return Entity(x, y, "%", "item_food", "Ration of Food", item=item, render_order=RenderOrder.ITEM)


def make_gold(x, y, amount):
    entity = Entity(x, y, "$", "item_gold", f"{amount} gold pieces", render_order=RenderOrder.ITEM)
    entity.gold_amount = amount
    return entity


def make_dagger(x, y):
    equippable = Equippable(EquipmentSlots.WEAPON, power_bonus=1)
    return Entity(x, y, "/", "item_weapon", "Dagger", equippable=equippable, render_order=RenderOrder.ITEM)


def make_short_sword(x, y):
    equippable = Equippable(EquipmentSlots.WEAPON, power_bonus=2)
    return Entity(x, y, "/", "item_weapon", "Short Sword", equippable=equippable, render_order=RenderOrder.ITEM)


def make_sword(x, y):
    equippable = Equippable(EquipmentSlots.WEAPON, power_bonus=3)
    return Entity(x, y, "/", "item_weapon", "Sword", equippable=equippable, render_order=RenderOrder.ITEM)


def make_battle_axe(x, y):
    equippable = Equippable(EquipmentSlots.WEAPON, power_bonus=5)
    return Entity(x, y, "/", "item_weapon", "Battle Axe", equippable=equippable, render_order=RenderOrder.ITEM)


def make_leather_armor(x, y):
    equippable = Equippable(EquipmentSlots.ARMOR, defense_bonus=1)
    return Entity(x, y, "[", "item_armor", "Leather Armor", equippable=equippable, render_order=RenderOrder.ITEM)


def make_chain_mail(x, y):
    equippable = Equippable(EquipmentSlots.ARMOR, defense_bonus=3)
    return Entity(x, y, "[", "item_armor", "Chain Mail", equippable=equippable, render_order=RenderOrder.ITEM)


def make_plate_armor(x, y):
    equippable = Equippable(EquipmentSlots.ARMOR, defense_bonus=5, max_hp_bonus=10)
    return Entity(x, y, "[", "item_armor", "Plate Armor", equippable=equippable, render_order=RenderOrder.ITEM)


def make_shield(x, y):
    equippable = Equippable(EquipmentSlots.SHIELD, defense_bonus=2)
    return Entity(x, y, ")", "item_armor", "Wooden Shield", equippable=equippable, render_order=RenderOrder.ITEM)


def make_tower_shield(x, y):
    equippable = Equippable(EquipmentSlots.SHIELD, defense_bonus=4, max_hp_bonus=5)
    return Entity(x, y, ")", "item_armor", "Tower Shield", equippable=equippable, render_order=RenderOrder.ITEM)


def make_amulet(x, y):
    return Entity(
        x,
        y,
        '"',
        "amulet",
        "Amulet of Yendor",
        render_order=RenderOrder.ITEM,
        always_visible=True,
        item=Item(),
    )
