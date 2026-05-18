from levelkit import healing_item, quest_item


ITEMS = [
    quest_item("My Quest Item", id="my_quest_item"),
    healing_item("My Healing Item", id="my_healing_item", heals=1),
]
