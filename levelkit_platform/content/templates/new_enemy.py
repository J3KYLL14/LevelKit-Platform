from levelkit import enemy


CHARACTER = enemy(
    "My Enemy",
    id="my_enemy",
    health=2,
    speed="slow",
    touch_damage=1,
    patrol="short",
)
