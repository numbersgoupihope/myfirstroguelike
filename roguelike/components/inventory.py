"""Holds an entity's carried items and mediates using/dropping them."""

from roguelike.message_log import Message


class Inventory:
    def __init__(self, capacity):
        self.capacity = capacity
        self.items = []
        self.owner = None

    def add_item(self, item):
        results = []
        if len(self.items) >= self.capacity:
            results.append(
                {
                    "item_added": None,
                    "message": Message(
                        "Your inventory is full, you cannot pick up the "
                        f"{item.name}.",
                        "msg_warning",
                    ),
                }
            )
        else:
            self.items.append(item)
            results.append(
                {
                    "item_added": item,
                    "message": Message(f"You pick up the {item.name}.", "msg_good"),
                }
            )
        return results

    def remove_item(self, item):
        if item in self.items:
            self.items.remove(item)

    def use(self, item_entity, **kwargs):
        results = []
        item_component = item_entity.item

        if item_component.use_function is None:
            if item_entity.equippable is not None:
                results.append({"equip": item_entity})
            else:
                results.append(
                    {
                        "message": Message(
                            f"The {item_entity.name} cannot be used.", "msg_info"
                        )
                    }
                )
            return results

        merged_kwargs = {**item_component.function_kwargs, **kwargs}
        use_results = item_component.use_function(self.owner, **merged_kwargs)

        for result in use_results:
            if result.get("consumed"):
                self.remove_item(item_entity)

        results.extend(use_results)
        return results

    def drop_item(self, item):
        results = []
        if self.owner.equipment is not None and self.owner.equipment.is_equipped(item):
            results.extend(self.owner.equipment.toggle_equip(item))

        item.x = self.owner.x
        item.y = self.owner.y
        self.remove_item(item)
        results.append(
            {"item_dropped": item, "message": Message(f"You drop the {item.name}.", "msg_info")}
        )
        return results
