"""Hunger clock. Only the player carries one, but it's a plain component so
nothing else needs to special-case "the player" by identity."""

from roguelike import constants


class Hunger:
    def __init__(self, max_value=constants.HUNGER_MAX):
        self.max_value = max_value
        self.current = max_value
        self.owner = None

    @property
    def state(self):
        if self.current <= constants.HUNGER_STARVING_THRESHOLD:
            return "starving"
        if self.current <= constants.HUNGER_HUNGRY_THRESHOLD:
            return "hungry"
        return "ok"

    def tick(self, amount=1):
        self.current = max(0, self.current - amount)

    def eat(self, amount):
        was_starving = self.state == "starving"
        self.current = min(self.max_value, self.current + amount)
        return was_starving
