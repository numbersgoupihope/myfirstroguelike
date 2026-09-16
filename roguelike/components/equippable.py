"""Marks an Item as wearable/wieldable and defines its stat bonuses."""

from enum import Enum


class EquipmentSlots(Enum):
    WEAPON = "weapon"
    ARMOR = "armor"
    SHIELD = "shield"


class Equippable:
    def __init__(self, slot, power_bonus=0, defense_bonus=0, max_hp_bonus=0):
        self.slot = slot
        self.power_bonus = power_bonus
        self.defense_bonus = defense_bonus
        self.max_hp_bonus = max_hp_bonus
        self.owner = None
