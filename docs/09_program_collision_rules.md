# 09 Program Collision Rules

Students program collision outcomes in:

```text
levelkit_platform/content/collision_rules.py
```

The engine detects when rectangles touch. These functions decide what happens
after that collision is found.

Examples:

```python
def player_hits_hazard(game, player, hazard):
    game.damage_player(1)
```

```python
def player_collects_pickup(game, player, pickup):
    game.collect_pickup(pickup)
```

```python
def player_reaches_win_zone(game, player, win_zone):
    game.win()
```

Useful game actions:

- `game.damage_player(amount)`
- `game.collect_pickup(pickup)`
- `game.set_checkpoint(checkpoint)`
- `game.say("message", speaker="Name")`
- `game.win()`
- `game.go_to("level_id", "spawn_id")`

Challenge ideas:

- Make hazards deal 2 damage instead of 1.
- Make a pickup fully heal the player.
- Make a checkpoint show a message.
- Make a win zone require a specific item first.
- Make an exit send the player to a different spawn.
