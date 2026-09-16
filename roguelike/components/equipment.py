"""Tracks what an entity has equipped in each slot and totals the bonuses."""

from roguelike.components.equippable import EquipmentSlots
from roguelike.message_log import Message


class Equipment:
    def __init__(self):
        self.slots = {
            EquipmentSlots.WEAPON: None,
            EquipmentSlots.ARMOR: None,
            EquipmentSlots.SHIELD: None,
        }
        self.owner = None

    @property
    def max_hp_bonus(self):
        return sum(
            item.equippable.max_hp_bonus for item in self.slots.values() if item
        )

    @property
    def power_bonus(self):
        return sum(item.equippable.power_bonus for item in self.slots.values() if item)

    @property
    def defense_bonus(self):
        return sum(
            item.equippable.defense_bonus for item in self.slots.values() if item
        )

    def is_equipped(self, item):
        return item in self.slots.values()

    def toggle_equip(self, item):
        """Equip an item, unequipping whatever currently occupies its slot.
        Equipping an already-equipped item takes it off instead."""
        results = []
        slot = item.equippable.slot

        if self.slots.get(slot) is item:
            self.slots[slot] = None
            results.append({"equipped": None, "unequipped": item})
            results.append(
                {"message": Message(f"You unequip the {item.name}.", "msg_info")}
            )
            return results

        old_item = self.slots.get(slot)
        if old_item is not None:
            results.append({"unequipped": old_item})
            results.append(
                {"message": Message(f"You unequip the {old_item.name}.", "msg_info")}
            )

        self.slots[slot] = item
        results.append({"equipped": item})
        results.append({"message": Message(f"You equip the {item.name}.", "msg_good")})
        return results
