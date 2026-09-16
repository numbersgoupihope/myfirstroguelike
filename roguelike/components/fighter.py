"""Combat statistics component. Attached to the player and every monster."""

from roguelike import combat
from roguelike.message_log import Message


class Fighter:
    def __init__(self, hp, defense, power, xp=0, on_hit=None):
        self.base_max_hp = hp
        self.hp = hp
        self.base_defense = defense
        self.base_power = power
        self.xp = xp  # XP awarded to whoever kills this entity
        # Optional callback(attacker_entity, target_entity, damage) invoked
        # after a successful hit, e.g. a spider injecting poison.
        self.on_hit = on_hit
        self.owner = None

    def _equipment_bonus(self, attr):
        equipment = getattr(self.owner, "equipment", None)
        if equipment is None:
            return 0
        return getattr(equipment, attr, 0)

    @property
    def max_hp(self):
        return self.base_max_hp + self._equipment_bonus("max_hp_bonus")

    @property
    def power(self):
        return self.base_power + self._equipment_bonus("power_bonus")

    @property
    def defense(self):
        return self.base_defense + self._equipment_bonus("defense_bonus")

    def take_damage(self, amount):
        results = []
        self.hp -= amount
        if self.hp <= 0:
            self.hp = 0
            results.append({"dead": self.owner})
        return results

    def heal(self, amount):
        self.hp = min(self.hp + amount, self.max_hp)

    def attack(self, target, rng=None):
        results = []
        damage, hit = combat.roll_attack(self.power, target.fighter.defense, rng=rng)
        attacker_name = self.owner.name.capitalize()
        target_name = target.name

        if not hit:
            results.append(
                {
                    "message": Message(
                        f"{attacker_name} attacks {target_name} but misses.",
                        "msg_info",
                    )
                }
            )
            return results

        color = "msg_bad" if self.owner.name == "you" else "msg_warning"
        results.append(
            {
                "message": Message(
                    f"{attacker_name} attacks {target_name} for {damage} hit points.",
                    color,
                )
            }
        )
        results.extend(target.fighter.take_damage(damage))

        if self.on_hit and target.fighter is not None:
            results.extend(self.on_hit(self.owner, target, damage))

        return results
