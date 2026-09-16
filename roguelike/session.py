"""All game logic and state, with zero dependency on curses.

Split out from :mod:`roguelike.engine` so the turn loop, combat resolution,
inventory handling, dungeon generation and save/load can be unit tested
directly -- curses can't be driven headlessly, but this class can."""

import random

from roguelike import constants, death_functions, fov, input_handlers, item_data, pathfinding, save_handling, world_gen
from roguelike.components.equipment import Equipment
from roguelike.components.fighter import Fighter
from roguelike.components.hunger import Hunger
from roguelike.components.inventory import Inventory
from roguelike.components.level import Level
from roguelike.components.status_effects import StatusEffects
from roguelike.entity import Entity, RenderOrder, get_blocking_entity
from roguelike.game_map import GameMap
from roguelike.game_states import GameStates
from roguelike.message_log import MessageLog


class GameSession:
    def __init__(self, rng=None, msg_width=constants.MSG_PANEL_WIDTH):
        self.rng = rng or random.Random()
        self.msg_width = msg_width
        self.message_log = MessageLog(msg_width)
        self.state = GameStates.MAIN_MENU
        self.previous_state = GameStates.PLAYERS_TURN
        self.player = None
        self.entities = []
        self.game_map = None
        self.dungeon_level = 1
        self.turn_count = 0
        self.visible_tiles = set()
        self.targeting_item = None
        self.cursor = (0, 0)
        self.inventory_mode = "use"
        self.history_scroll = 0

    # ------------------------------------------------------------------
    # Game lifecycle
    # ------------------------------------------------------------------

    def new_game(self):
        self.dungeon_level = 1
        self.turn_count = 0
        self.message_log = MessageLog(self.msg_width)

        player = Entity(
            0,
            0,
            "@",
            "player",
            "you",
            blocks=True,
            render_order=RenderOrder.PLAYER,
            fighter=Fighter(
                hp=constants.PLAYER_BASE_HP,
                defense=constants.PLAYER_BASE_DEFENSE,
                power=constants.PLAYER_BASE_POWER,
            ),
            inventory=Inventory(constants.INVENTORY_CAPACITY),
            level=Level(),
            equipment=Equipment(),
            status_effects=StatusEffects(),
            hunger=Hunger(),
        )
        player.gold = 0
        self.player = player

        dagger = item_data.make_dagger(0, 0)
        armor = item_data.make_leather_armor(0, 0)
        player.inventory.items.extend([dagger, armor])
        self.process_results(player.equipment.toggle_equip(dagger))
        self.process_results(player.equipment.toggle_equip(armor))
        player.inventory.items.append(item_data.make_food_ration(0, 0))
        player.inventory.items.append(item_data.make_healing_potion(0, 0))

        self.generate_floor(arrival="down")
        self.message_log.add(
            "Welcome to the Depths of Yendor. Find the Amulet and escape alive!",
            "title",
        )
        self.state = GameStates.PLAYERS_TURN

    def reset_to_menu(self):
        self.player = None
        self.entities = []
        self.game_map = None
        self.state = GameStates.MAIN_MENU

    def generate_floor(self, arrival="down"):
        self.game_map = GameMap(constants.MAP_WIDTH, constants.MAP_HEIGHT, self.dungeon_level)
        self.game_map.make_map(
            constants.MAX_ROOMS,
            constants.ROOM_MIN_SIZE,
            constants.ROOM_MAX_SIZE,
            self.player,
            rng=self.rng,
        )
        if arrival == "up":
            self.player.x, self.player.y = self.game_map.downstairs_pos

        self.entities = [self.player]
        world_gen.place_stairs(self.game_map, self.entities)
        world_gen.populate_dungeon(self.game_map, self.entities, rng=self.rng)
        self.recompute_fov()

    def recompute_fov(self):
        self.visible_tiles = fov.compute_fov(
            self.game_map, self.player.x, self.player.y, constants.FOV_RADIUS
        )

    # ------------------------------------------------------------------
    # Result processing
    # ------------------------------------------------------------------

    def process_results(self, results):
        for result in results:
            message = result.get("message")
            if message:
                self.message_log.add(message.text, message.color)

            dead_entity = result.get("dead")
            if dead_entity is not None:
                if dead_entity is self.player:
                    self.process_results(death_functions.kill_player(self.player))
                    self.state = GameStates.PLAYER_DEAD
                    save_handling.delete_save()
                else:
                    self.process_results(death_functions.kill_monster(dead_entity))

            equip = result.get("equip")
            if equip is not None:
                self.process_results(self.player.equipment.toggle_equip(equip))

    def _apply_player_damage_results(self, results):
        """Route results from a player-initiated attack/spell through
        process_results, but first bank XP for anything it killed (corpse
        conversion nulls the fighter component, so xp must be read first)."""
        xp_total = 0
        for result in results:
            dead = result.get("dead")
            if dead is not None and dead is not self.player and dead.fighter is not None:
                xp_total += dead.fighter.xp

        self.process_results(results)

        if xp_total and self.state != GameStates.PLAYER_DEAD:
            self.message_log.add(f"You gain {xp_total} experience points.", "msg_good")
            if self.player.level.add_xp(xp_total):
                self.message_log.add(
                    "Your battle prowess grows -- you feel yourself become stronger!",
                    "title",
                )
                self.state = GameStates.LEVEL_UP

    def check_trap(self, entity):
        tile = self.game_map.tiles[entity.y][entity.x]
        if tile.trap is None or tile.trap.discovered:
            return []
        return tile.trap.trigger(entity)

    # ------------------------------------------------------------------
    # Player turn
    # ------------------------------------------------------------------

    def process_player_action(self, action):
        player = self.player
        turn_taken = False

        if "move" in action:
            dx, dy = action["move"]
            if player.status_effects and player.status_effects.is_confused:
                dx, dy = self.rng.choice(list(set(input_handlers.MOVE_KEYS.values())))
                self.message_log.add("You stumble around in confusion!", "msg_warning")

            dest_x, dest_y = player.x + dx, player.y + dy
            turn_taken = True
            if self.game_map.in_bounds(dest_x, dest_y) and not self.game_map.tiles[dest_y][dest_x].blocked:
                target = get_blocking_entity(self.entities, dest_x, dest_y)
                if target is not None and target.fighter is not None:
                    self._apply_player_damage_results(player.fighter.attack(target, rng=self.rng))
                else:
                    player.move(dx, dy)
                    self.process_results(self.check_trap(player))
            else:
                self.message_log.add("You can't move there.", "msg_info")
                turn_taken = False

        elif action.get("wait"):
            turn_taken = True

        elif action.get("pickup"):
            turn_taken = self._handle_pickup()

        elif action.get("show_inventory"):
            if player.inventory.items:
                self.inventory_mode = "use"
                self.state = GameStates.SHOW_INVENTORY
            else:
                self.message_log.add("Your inventory is empty.", "msg_info")

        elif action.get("drop_inventory"):
            if player.inventory.items:
                self.inventory_mode = "drop"
                self.state = GameStates.DROP_INVENTORY
            else:
                self.message_log.add("You have nothing to drop.", "msg_info")

        elif "take_stairs" in action:
            turn_taken = self._handle_stairs(action["take_stairs"])

        elif action.get("character_screen"):
            self.previous_state = self.state
            self.state = GameStates.CHARACTER_SCREEN

        elif action.get("help"):
            self.previous_state = self.state
            self.state = GameStates.HELP_SCREEN

        elif action.get("message_history"):
            self.previous_state = self.state
            self.history_scroll = 0
            self.state = GameStates.MESSAGE_HISTORY

        elif action.get("quit"):
            save_handling.save_game(self.to_save_state())
            self.state = GameStates.EXIT

        if turn_taken:
            self._finish_player_turn()

    def _finish_player_turn(self):
        self.turn_count += 1
        self.recompute_fov()
        if self.state == GameStates.PLAYERS_TURN:
            self.state = GameStates.ENEMY_TURN

    def _handle_pickup(self):
        player = self.player
        here = [
            e
            for e in self.entities
            if e.x == player.x and e.y == player.y and (e.item is not None or getattr(e, "gold_amount", None))
        ]
        if not here:
            self.message_log.add("There is nothing here to pick up.", "msg_info")
            return False

        item = here[0]
        gold_amount = getattr(item, "gold_amount", None)
        if gold_amount:
            player.gold = getattr(player, "gold", 0) + gold_amount
            self.message_log.add(f"You pick up {gold_amount} gold pieces.", "item_gold")
            self.entities.remove(item)
            return True

        add_results = player.inventory.add_item(item)
        picked = any(r.get("item_added") for r in add_results)
        self.message_log.extend_results(add_results)
        if picked:
            self.entities.remove(item)
            if item.name == "Amulet of Yendor":
                self.message_log.add(
                    "You feel a malevolent presence stir in the depths below...", "msg_crit"
                )
        return picked

    def _handle_stairs(self, direction):
        player = self.player
        stairs_here = next(
            (
                e
                for e in self.entities
                if e.x == player.x and e.y == player.y and e.stairs and e.stairs.direction == direction
            ),
            None,
        )
        if stairs_here is None:
            self.message_log.add(f"There are no stairs {direction} here.", "msg_info")
            return False

        if direction == "down":
            self.dungeon_level += 1
            self.message_log.add(
                f"You descend deeper into the dungeon... (level {self.dungeon_level})", "msg_info"
            )
            self.generate_floor(arrival="down")
            return True

        if self.dungeon_level == 1:
            if self.has_amulet():
                self.state = GameStates.VICTORY
                save_handling.delete_save()
            else:
                self.previous_state = self.state
                self.state = GameStates.CONFIRM_LEAVE
            return False

        self.dungeon_level -= 1
        self.message_log.add(f"You climb back up to level {self.dungeon_level}.", "msg_info")
        self.generate_floor(arrival="up")
        return True

    def has_amulet(self):
        return any(i.name == "Amulet of Yendor" for i in self.player.inventory.items)

    def handle_inventory_selection(self, index):
        player = self.player
        if index >= len(player.inventory.items):
            return
        item = player.inventory.items[index]

        if self.inventory_mode == "drop":
            self.process_results(player.inventory.drop_item(item))
            self.entities.append(item)
            self.state = GameStates.PLAYERS_TURN
            self._finish_player_turn()
            return

        if item.item is not None and item.item.targeting:
            self.targeting_item = item
            self.cursor = (player.x, player.y)
            self.state = GameStates.TARGETING
            message = item.item.targeting_message
            if message:
                self.message_log.add(message.text, message.color)
            return

        results = player.inventory.use(
            item, entities=self.entities, fov_tiles=self.visible_tiles, game_map=self.game_map, rng=self.rng
        )
        self.state = GameStates.PLAYERS_TURN
        self._apply_player_damage_results(results)
        self._finish_player_turn()

    def resolve_targeting(self):
        player = self.player
        item = self.targeting_item
        target_x, target_y = self.cursor
        results = player.inventory.use(
            item,
            entities=self.entities,
            fov_tiles=self.visible_tiles,
            game_map=self.game_map,
            target_x=target_x,
            target_y=target_y,
            rng=self.rng,
        )
        self.targeting_item = None
        self.state = GameStates.PLAYERS_TURN
        self._apply_player_damage_results(results)
        self._finish_player_turn()

    def apply_level_up(self, stat):
        fighter = self.player.fighter
        if stat == "power":
            fighter.base_power += 1
            self.message_log.add("Your muscles bulge with newfound strength.", "msg_good")
        elif stat == "hp":
            fighter.base_max_hp += 10
            fighter.hp += 10
            self.message_log.add("Your body toughens; your maximum health increases.", "msg_good")
        elif stat == "defense":
            fighter.base_defense += 1
            self.message_log.add("Your reflexes sharpen; you feel better protected.", "msg_good")

    # ------------------------------------------------------------------
    # Enemy turn
    # ------------------------------------------------------------------

    def run_enemy_turn(self):
        distance_map = pathfinding.compute_distance_map(self.game_map, self.player.x, self.player.y)

        for entity in list(self.entities):
            if entity.ai is None or entity.fighter is None:
                continue
            results = entity.ai.take_turn(
                self.player, self.visible_tiles, self.game_map, self.entities, distance_map, rng=self.rng
            )
            results.extend(self.check_trap(entity))
            self.process_results(results)
            if self.state == GameStates.PLAYER_DEAD:
                return

        for entity in list(self.entities):
            if entity.status_effects is None or entity.fighter is None:
                continue
            self.process_results(entity.status_effects.process_turn())
            if self.state == GameStates.PLAYER_DEAD:
                return

        if self.player.hunger is not None:
            self.player.hunger.tick(1)
            if (
                self.player.hunger.state == "starving"
                and self.turn_count % constants.STARVING_DAMAGE_PERIOD == 0
            ):
                self.message_log.add("You are starving! You must find food.", "msg_bad")
                self.process_results(self.player.fighter.take_damage(1))
                if self.state == GameStates.PLAYER_DEAD:
                    return

        self.state = GameStates.PLAYERS_TURN

    # ------------------------------------------------------------------
    # Save / load
    # ------------------------------------------------------------------

    def to_save_state(self):
        return {
            "player": self.player,
            "entities": self.entities,
            "game_map": self.game_map,
            "dungeon_level": self.dungeon_level,
            "turn_count": self.turn_count,
            "messages": self.message_log.messages,
            "rng_state": self.rng.getstate(),
        }

    def load_from_state(self, state):
        self.player = state["player"]
        self.entities = state["entities"]
        self.game_map = state["game_map"]
        self.dungeon_level = state["dungeon_level"]
        self.turn_count = state["turn_count"]
        self.message_log = MessageLog(self.msg_width)
        self.message_log.messages = state["messages"]
        self.rng.setstate(state["rng_state"])
        self.recompute_fov()
        self.state = GameStates.PLAYERS_TURN

    def describe_item_line(self, letter, item):
        label = item.name
        if self.player.equipment and self.player.equipment.is_equipped(item):
            label += " (equipped)"
        return f"({letter}) {label}"
