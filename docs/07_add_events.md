# 07 Add Events

Simple event hooks live in:

```text
levelkit_platform/content/events.py
```

Show a message when the player enters a level:

```python
from levelkit import when_enter_level


when_enter_level("meadow", say="Welcome to the meadow.")
```

Show a message when the player collects an item:

```python
from levelkit import when_pickup


when_pickup("sun_orb", say="You found the Sun Orb!")
```

Advanced students can use a function:

```python
def reward_player(game, pickup):
    game.player.health = game.player.max_health


when_pickup("sun_orb", function=reward_player)
```
