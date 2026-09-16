import random

from roguelike.components.equipment import Equipment
from roguelike.components.equippable import EquipmentSlots, Equippable
from roguelike.components.fighter import Fighter
from roguelike.components.hunger import Hunger
from roguelike.components.inventory import Inventory
from roguelike.components.item import Item
from roguelike.components.level import Level
from roguelike.components.status_effects import StatusEffects
from roguelike.components.trap import Trap
from roguelike.entity import Entity


def make_fighter_entity(name, hp=20, defense=1, power=5, xp=10, **kwargs):
    return Entity(
        0,
        0,
        "x",
        "default",
        name,
        blocks=True,
        fighter=Fighter(hp=hp, defense=defense, power=power, xp=xp),
        status_effects=StatusEffects(),
        **kwargs,
    )


# --- Fighter -----------------------------------------------------------


def test_take_damage_reports_dead_at_zero_hp():
    e = make_fighter_entity("rat", hp=5)
    results = e.fighter.take_damage(5)
    assert e.fighter.hp == 0
    assert results == [{"dead": e}]


def test_take_damage_never_goes_negative():
    e = make_fighter_entity("rat", hp=5)
    e.fighter.take_damage(999)
    assert e.fighter.hp == 0


def test_heal_caps_at_max_hp():
    e = make_fighter_entity("rat", hp=20)
    e.fighter.hp = 5
    e.fighter.heal(999)
    assert e.fighter.hp == e.fighter.max_hp


class FixedRandom(random.Random):
    """A Random whose random()/randint() are pinned, so combat outcomes are
    fully deterministic for testing."""

    def __init__(self, roll):
        super().__init__()
        self.roll = roll

    def random(self):
        return self.roll

    def randint(self, a, b):
        return a


def test_attack_hit_path_deals_damage_and_logs_message():
    attacker = make_fighter_entity("you", power=10, defense=1)
    target = make_fighter_entity("rat", hp=20, defense=0)
    results = attacker.fighter.attack(target, rng=FixedRandom(0.0))
    assert target.fighter.hp < 20
    assert any(r.get("message") for r in results)


def test_attack_miss_path_deals_no_damage():
    attacker = make_fighter_entity("you", power=1, defense=0)
    target = make_fighter_entity("rat", hp=20, defense=0)
    results = attacker.fighter.attack(target, rng=FixedRandom(0.999))
    assert target.fighter.hp == 20
    assert any("misses" in r["message"].text for r in results if r.get("message"))


def test_on_hit_callback_fires_after_successful_damage():
    events = []

    def on_hit(attacker, target, damage):
        events.append(damage)
        return []

    attacker = Entity(
        0, 0, "s", "default", "spider", fighter=Fighter(hp=10, defense=0, power=50, on_hit=on_hit)
    )
    target = make_fighter_entity("you", hp=100, defense=0)

    attacker.fighter.attack(target, rng=FixedRandom(0.0))
    assert events, "on_hit should have fired on a successful hit"


def test_equipment_bonuses_apply_to_fighter():
    player = make_fighter_entity("you", hp=30, defense=1, power=4)
    player.equipment = Equipment()
    player.equipment.owner = player
    sword = Entity(0, 0, "/", "item_weapon", "Sword", equippable=Equippable(EquipmentSlots.WEAPON, power_bonus=3))
    player.equipment.toggle_equip(sword)
    assert player.fighter.power == 7


# --- Equipment / Equippable ---------------------------------------------


def test_toggle_equip_swaps_slot_contents():
    owner = Entity(0, 0, "@", "player", "you")
    owner.equipment = Equipment()
    owner.equipment.owner = owner

    dagger = Entity(0, 0, "/", "item_weapon", "Dagger", equippable=Equippable(EquipmentSlots.WEAPON, power_bonus=1))
    sword = Entity(0, 0, "/", "item_weapon", "Sword", equippable=Equippable(EquipmentSlots.WEAPON, power_bonus=3))

    owner.equipment.toggle_equip(dagger)
    assert owner.equipment.is_equipped(dagger)

    owner.equipment.toggle_equip(sword)
    assert owner.equipment.is_equipped(sword)
    assert not owner.equipment.is_equipped(dagger)


def test_toggle_equip_twice_unequips():
    owner = Entity(0, 0, "@", "player", "you")
    owner.equipment = Equipment()
    owner.equipment.owner = owner
    shield = Entity(0, 0, ")", "item_armor", "Shield", equippable=Equippable(EquipmentSlots.SHIELD, defense_bonus=2))
    owner.equipment.toggle_equip(shield)
    assert owner.equipment.is_equipped(shield)
    owner.equipment.toggle_equip(shield)
    assert not owner.equipment.is_equipped(shield)


# --- Inventory -----------------------------------------------------------


def test_inventory_add_respects_capacity():
    owner = Entity(0, 0, "@", "player", "you")
    inv = Inventory(2)
    inv.owner = owner
    owner.inventory = inv

    a = Entity(0, 0, "!", "item_potion", "Potion A", item=Item())
    b = Entity(0, 0, "!", "item_potion", "Potion B", item=Item())
    c = Entity(0, 0, "!", "item_potion", "Potion C", item=Item())

    assert inv.add_item(a)[0]["item_added"] is a
    assert inv.add_item(b)[0]["item_added"] is b
    assert inv.add_item(c)[0]["item_added"] is None
    assert len(inv.items) == 2


def test_inventory_use_consumes_item():
    owner = Entity(0, 0, "@", "player", "you", fighter=Fighter(hp=10, defense=0, power=1))
    owner.fighter.hp = 5
    inv = Inventory(10)
    inv.owner = owner
    owner.inventory = inv

    def heal_fn(user, amount, **kwargs):
        user.fighter.heal(amount)
        return [{"consumed": True}]

    potion = Entity(0, 0, "!", "item_potion", "Potion", item=Item(use_function=heal_fn, amount=5))
    inv.items.append(potion)

    inv.use(potion)
    assert owner.fighter.hp == 10
    assert potion not in inv.items


def test_inventory_drop_unequips_first():
    owner = Entity(3, 4, "@", "player", "you")
    inv = Inventory(10)
    inv.owner = owner
    owner.inventory = inv
    owner.equipment = Equipment()
    owner.equipment.owner = owner

    dagger = Entity(0, 0, "/", "item_weapon", "Dagger", equippable=Equippable(EquipmentSlots.WEAPON, power_bonus=1))
    inv.items.append(dagger)
    owner.equipment.toggle_equip(dagger)
    assert owner.equipment.is_equipped(dagger)

    inv.drop_item(dagger)
    assert not owner.equipment.is_equipped(dagger)
    assert dagger.x == 3 and dagger.y == 4
    assert dagger not in inv.items


# --- Level -----------------------------------------------------------------


def test_level_up_rolls_over_excess_xp():
    level = Level(current_level=1, current_xp=0, level_up_base=100, level_up_factor=0)
    leveled = level.add_xp(150)
    assert leveled
    assert level.current_level == 2
    assert level.current_xp == 50


def test_level_up_false_when_not_enough_xp():
    level = Level(current_level=1, current_xp=0, level_up_base=100, level_up_factor=0)
    assert level.add_xp(10) is False
    assert level.current_level == 1


# --- Hunger ------------------------------------------------------------


def test_hunger_state_thresholds():
    h = Hunger(max_value=1000)
    assert h.state == "ok"
    h.current = 200
    assert h.state == "hungry"
    h.current = 10
    assert h.state == "starving"


def test_hunger_tick_and_eat_clamp():
    h = Hunger(max_value=100)
    h.current = 100
    h.eat(50)
    assert h.current == 100
    h.tick(1000)
    assert h.current == 0


# --- StatusEffects -------------------------------------------------------


def test_poison_ticks_down_and_damages():
    e = make_fighter_entity("you", hp=20, defense=0)
    e.status_effects.apply_poison(2, 3)
    results = e.status_effects.process_turn()
    assert e.fighter.hp == 17
    assert e.status_effects.poison_turns == 1
    assert any(r.get("message") for r in results)


def test_confusion_expires_and_reports_it():
    e = make_fighter_entity("you", hp=20)
    e.status_effects.apply_confusion(1)
    results = e.status_effects.process_turn()
    assert e.status_effects.confusion_turns == 0
    assert any("no longer confused" in r["message"].text for r in results if r.get("message"))


# --- Trap ----------------------------------------------------------------


def test_dart_trap_damages_and_discovers():
    e = make_fighter_entity("you", hp=20, defense=0)
    trap = Trap("dart", damage=4)
    assert not trap.discovered
    results = trap.trigger(e)
    assert trap.discovered
    assert e.fighter.hp == 16
    assert any(r.get("message") for r in results)


def test_poison_gas_trap_applies_status():
    e = make_fighter_entity("you", hp=20, defense=0)
    trap = Trap("poison_gas", damage=2, poison_turns=5)
    trap.trigger(e)
    assert e.status_effects.is_poisoned
    assert e.status_effects.poison_turns == 5
