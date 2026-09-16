"""Hidden dungeon hazards embedded in a floor tile (not a walkable Entity)."""

from roguelike.message_log import Message


class Trap:
    def __init__(self, kind, damage=0, poison_turns=0, confusion_turns=0, discovered=False):
        self.kind = kind
        self.damage = damage
        self.poison_turns = poison_turns
        self.confusion_turns = confusion_turns
        self.discovered = discovered
        self.owner = None

    def trigger(self, entity):
        results = []
        self.discovered = True
        name = entity.name.capitalize()

        if self.kind == "dart":
            results.append(
                {
                    "message": Message(
                        f"A dart trap fires! {name} is hit for {self.damage} damage.",
                        "msg_bad",
                    )
                }
            )
            if entity.fighter:
                results.extend(entity.fighter.take_damage(self.damage))
        elif self.kind == "poison_gas":
            results.append(
                {
                    "message": Message(
                        f"A cloud of poison gas envelops {name}!", "msg_bad"
                    )
                }
            )
            if entity.status_effects:
                entity.status_effects.apply_poison(self.poison_turns, self.damage)
        elif self.kind == "confusion":
            results.append(
                {
                    "message": Message(
                        f"Runes flash -- {name} feels disoriented!", "msg_bad"
                    )
                }
            )
            if entity.status_effects:
                entity.status_effects.apply_confusion(self.confusion_turns)
        elif self.kind == "alarm":
            results.append(
                {
                    "message": Message(
                        "A screeching alarm trap echoes through the dungeon!",
                        "msg_warning",
                    )
                }
            )
        elif self.kind == "pit":
            results.append(
                {
                    "message": Message(
                        f"{name} falls into a concealed pit for {self.damage} damage!",
                        "msg_bad",
                    )
                }
            )
            if entity.fighter:
                results.extend(entity.fighter.take_damage(self.damage))

        return results
