"""Timed status effects (poison, confusion) usable by player and monsters
alike. Kept as one component so AI and input handling both just check
``owner.status_effects`` instead of the classic "swap the AI class" trick."""

from roguelike.message_log import Message


class StatusEffects:
    def __init__(self):
        self.confusion_turns = 0
        self.poison_turns = 0
        self.poison_damage = 1
        self.owner = None

    @property
    def is_confused(self):
        return self.confusion_turns > 0

    @property
    def is_poisoned(self):
        return self.poison_turns > 0

    def apply_confusion(self, turns):
        self.confusion_turns = max(self.confusion_turns, turns)

    def apply_poison(self, turns, damage_per_turn):
        self.poison_turns = max(self.poison_turns, turns)
        self.poison_damage = max(self.poison_damage, damage_per_turn)

    def process_turn(self):
        """Advance timers by one turn. Returns action-result dicts."""
        results = []
        owner = self.owner
        name = owner.name.capitalize()

        if self.poison_turns > 0:
            self.poison_turns -= 1
            if owner.fighter is not None:
                results.append(
                    {
                        "message": Message(
                            f"{name} writhes in pain from poison ({self.poison_damage} damage).",
                            "msg_bad",
                        )
                    }
                )
                results.extend(owner.fighter.take_damage(self.poison_damage))

        if self.confusion_turns > 0:
            self.confusion_turns -= 1
            if self.confusion_turns == 0:
                results.append(
                    {"message": Message(f"{name} is no longer confused.", "msg_info")}
                )

        return results
