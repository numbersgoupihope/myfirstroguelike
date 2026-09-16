import random

from roguelike import constants, item_data, monster_data, save_handling
from roguelike.components.trap import Trap
from roguelike.entity import get_blocking_entity
from roguelike.game_states import GameStates
from roguelike.session import GameSession


class FixedRandom(random.Random):
    """Deterministic stand-in RNG: always "rolls" low, so combat always
    hits with the smallest possible variance/mitigation."""

    def random(self):
        return 0.0

    def randint(self, a, b):
        return a


def new_session(rng=None):
    session = GameSession(rng=rng or FixedRandom())
    session.new_game()
    return session


# --- Basic setup -----------------------------------------------------------


def test_new_game_gives_starting_gear_and_position():
    session = new_session()
    player = session.player
    assert player.fighter.hp == constants.PLAYER_BASE_HP
    names = {i.name for i in player.inventory.items}
    assert "Dagger" in names
    assert "Leather Armor" in names
    assert session.player.equipment.is_equipped(
        next(i for i in player.inventory.items if i.name == "Dagger")
    )
    assert not session.game_map.tiles[player.y][player.x].blocked
    assert session.state == GameStates.PLAYERS_TURN


def test_move_into_wall_does_not_consume_a_turn():
    session = new_session()
    # Every tile outside the map is a "wall" for movement purposes.
    session.player.x, session.player.y = 0, 0
    turns_before = session.turn_count
    session.process_player_action({"move": (-1, -1)})
    assert session.turn_count == turns_before
    assert session.state == GameStates.PLAYERS_TURN


def test_waiting_advances_turn_and_hands_off_to_enemy_turn():
    session = new_session()
    session.entities = [session.player]  # no monsters to complicate this
    turns_before = session.turn_count
    session.process_player_action({"wait": True})
    assert session.turn_count == turns_before + 1
    assert session.state == GameStates.ENEMY_TURN


# --- Combat ------------------------------------------------------------


def test_moving_into_a_monster_attacks_instead_of_moving():
    session = new_session()
    player = session.player
    rat = monster_data.make_rat(player.x + 1, player.y)
    rat.fighter.hp = 100
    session.game_map.tiles[rat.y][rat.x].blocked = False
    session.entities.append(rat)

    session.process_player_action({"move": (1, 0)})

    assert player.x != rat.x or player.y != rat.y  # player did not move into the monster
    assert rat.fighter.hp < 100


def test_killing_a_monster_awards_xp_and_removes_it_from_play():
    session = new_session()
    player = session.player
    rat = monster_data.make_rat(player.x + 1, player.y)
    rat.fighter.hp = 1
    session.game_map.tiles[rat.y][rat.x].blocked = False
    session.entities.append(rat)

    session.process_player_action({"move": (1, 0)})

    assert rat.fighter is None  # converted to a corpse
    assert rat not in [e for e in session.entities if e.blocks]
    assert session.player.level.current_xp > 0 or session.state == GameStates.LEVEL_UP


def test_enough_xp_triggers_level_up_state():
    session = new_session()
    session.player.level.level_up_base = 1
    session.player.level.level_up_factor = 0
    player = session.player
    rat = monster_data.make_rat(player.x + 1, player.y)
    rat.fighter.hp = 1
    session.game_map.tiles[rat.y][rat.x].blocked = False
    session.entities.append(rat)

    session.process_player_action({"move": (1, 0)})

    assert session.state == GameStates.LEVEL_UP


def test_apply_level_up_power_increases_fighter_power():
    session = new_session()
    before = session.player.fighter.power
    session.apply_level_up("power")
    assert session.player.fighter.power == before + 1


def test_apply_level_up_hp_increases_max_and_current_hp():
    session = new_session()
    before_max = session.player.fighter.max_hp
    before_hp = session.player.fighter.hp
    session.apply_level_up("hp")
    assert session.player.fighter.max_hp == before_max + 10
    assert session.player.fighter.hp == before_hp + 10


# --- Items / inventory ---------------------------------------------------


def test_pickup_gold_increases_gold_without_using_inventory_slot():
    session = new_session()
    player = session.player
    gold = item_data.make_gold(player.x, player.y, 50)
    session.entities.append(gold)
    slots_before = len(player.inventory.items)

    session.process_player_action({"pickup": True})

    assert player.gold == 50
    assert len(player.inventory.items) == slots_before
    assert gold not in session.entities


def test_pickup_item_adds_to_inventory_and_removes_from_map():
    session = new_session()
    player = session.player
    potion = item_data.make_healing_potion(player.x, player.y)
    session.entities.append(potion)

    session.process_player_action({"pickup": True})

    assert potion in player.inventory.items
    assert potion not in session.entities


def test_pickup_amulet_logs_ominous_message():
    session = new_session()
    player = session.player
    amulet = item_data.make_amulet(player.x, player.y)
    session.entities.append(amulet)

    session.process_player_action({"pickup": True})

    assert session.has_amulet()
    assert any("malevolent" in m.text for m in session.message_log.messages)


def test_use_healing_potion_heals_and_consumes():
    session = new_session()
    player = session.player
    player.fighter.hp = 5
    potion = item_data.make_healing_potion(0, 0)
    player.inventory.items.append(potion)

    session.inventory_mode = "use"
    session.handle_inventory_selection(player.inventory.items.index(potion))

    assert player.fighter.hp == 20  # 5 + 15 from make_healing_potion
    assert potion not in player.inventory.items
    assert session.state == GameStates.ENEMY_TURN


def test_equip_item_from_inventory_via_use():
    session = new_session()
    player = session.player
    sword = item_data.make_sword(0, 0)
    player.inventory.items.append(sword)

    session.inventory_mode = "use"
    session.handle_inventory_selection(player.inventory.items.index(sword))

    assert player.equipment.is_equipped(sword)


def test_drop_item_places_it_back_on_the_map_and_unequips():
    session = new_session()
    player = session.player
    dagger = next(i for i in player.inventory.items if i.name == "Dagger")

    session.inventory_mode = "drop"
    session.handle_inventory_selection(player.inventory.items.index(dagger))

    assert dagger not in player.inventory.items
    assert dagger in session.entities
    assert not player.equipment.is_equipped(dagger)
    assert dagger.x == player.x and dagger.y == player.y


def test_targeting_scroll_flow_damages_area():
    session = new_session()
    player = session.player
    scroll = item_data.make_fireball_scroll(0, 0)
    player.inventory.items.append(scroll)

    monster = monster_data.make_rat(player.x + 1, player.y)
    monster.fighter.hp = 30
    session.game_map.tiles[monster.y][monster.x].blocked = False
    session.entities.append(monster)

    session.inventory_mode = "use"
    session.handle_inventory_selection(player.inventory.items.index(scroll))
    assert session.state == GameStates.TARGETING

    session.cursor = (monster.x, monster.y)
    session.resolve_targeting()

    assert monster.fighter.hp < 30
    assert session.targeting_item is None
    assert session.state in (GameStates.ENEMY_TURN, GameStates.LEVEL_UP)


def test_cancelling_targeting_keeps_the_item():
    session = new_session()
    player = session.player
    scroll = item_data.make_fireball_scroll(0, 0)
    player.inventory.items.append(scroll)
    session.inventory_mode = "use"
    session.handle_inventory_selection(player.inventory.items.index(scroll))
    assert session.state == GameStates.TARGETING

    session.targeting_item = None
    session.state = GameStates.PLAYERS_TURN

    assert scroll in player.inventory.items


# --- Traps ---------------------------------------------------------------


def test_player_triggers_trap_when_moving_onto_it():
    session = new_session()
    player = session.player
    gm = session.game_map

    target = None
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nx, ny = player.x + dx, player.y + dy
        if (
            gm.in_bounds(nx, ny)
            and not gm.tiles[ny][nx].blocked
            and get_blocking_entity(session.entities, nx, ny) is None
        ):
            target = (dx, dy, nx, ny)
            break
    assert target is not None
    dx, dy, nx, ny = target

    gm.tiles[ny][nx].trap = Trap("dart", damage=5)
    hp_before = player.fighter.hp

    session.process_player_action({"move": (dx, dy)})

    assert gm.tiles[ny][nx].trap.discovered
    assert player.fighter.hp == hp_before - 5


# --- Stairs / win-loss conditions -----------------------------------------


def test_stairs_down_increments_depth_and_regenerates_the_map():
    session = new_session()
    old_map = session.game_map
    down_x, down_y = session.game_map.downstairs_pos
    session.player.x, session.player.y = down_x, down_y

    session.process_player_action({"take_stairs": "down"})

    assert session.dungeon_level == 2
    assert session.game_map is not old_map
    assert session.state == GameStates.ENEMY_TURN


def test_stairs_up_from_level_one_without_amulet_asks_for_confirmation():
    session = new_session()
    up_x, up_y = session.game_map.upstairs_pos
    session.player.x, session.player.y = up_x, up_y

    session.process_player_action({"take_stairs": "up"})

    assert session.state == GameStates.CONFIRM_LEAVE


def test_stairs_up_from_level_one_with_amulet_wins_the_game():
    session = new_session()
    amulet = item_data.make_amulet(0, 0)
    session.player.inventory.items.append(amulet)
    up_x, up_y = session.game_map.upstairs_pos
    session.player.x, session.player.y = up_x, up_y

    session.process_player_action({"take_stairs": "up"})

    assert session.state == GameStates.VICTORY


def test_deep_stairs_up_returns_to_shallower_level():
    session = new_session()
    session.dungeon_level = 3
    session.generate_floor(arrival="down")
    up_x, up_y = session.game_map.upstairs_pos
    session.player.x, session.player.y = up_x, up_y

    session.process_player_action({"take_stairs": "up"})

    assert session.dungeon_level == 2
    assert session.state == GameStates.ENEMY_TURN


# --- Hunger --------------------------------------------------------------


def test_starving_player_takes_periodic_damage():
    session = new_session()
    session.entities = [session.player]  # isolate from monster AI
    session.player.hunger.current = 0
    session.turn_count = constants.STARVING_DAMAGE_PERIOD
    hp_before = session.player.fighter.hp

    session.state = GameStates.ENEMY_TURN
    session.run_enemy_turn()

    assert session.player.fighter.hp == hp_before - 1


# --- Save / load -----------------------------------------------------------


def test_save_and_load_round_trip():
    session = new_session()
    session.player.gold = 42
    session.turn_count = 17
    save_handling.save_game(session.to_save_state())

    loaded = GameSession()
    loaded.load_from_state(save_handling.load_game())

    assert loaded.player.gold == 42
    assert loaded.turn_count == 17
    assert loaded.dungeon_level == session.dungeon_level
    assert len(loaded.entities) == len(session.entities)
    assert loaded.state == GameStates.PLAYERS_TURN
