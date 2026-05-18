# 08 Program Player Controls

Students program player input in:

```text
levelkit_platform/content/player_controls.py
```

The engine still handles gravity and collision detection. This file decides what
the player tries to do when keys or mouse buttons are pressed.

```python
def control_player(player, keyboard, mouse, dt):
    player.velocity.x = 0

    if keyboard.left:
        player.velocity.x = -player.speed
        player.facing = -1

    if keyboard.right:
        player.velocity.x = player.speed
        player.facing = 1

    if keyboard.space and player.grounded:
        player.velocity.y = -player.jump_power
        player.grounded = False

    return {
        "melee": keyboard.j or mouse.left,
        "shoot": keyboard.k or mouse.right,
    }
```

## Keyboard Names

Use these names in code:

| Key | Code |
| --- | --- |
| Left arrow | `keyboard.left` |
| Right arrow | `keyboard.right` |
| Up arrow | `keyboard.up` |
| Down arrow | `keyboard.down` |
| Space | `keyboard.space` |
| Shift | `keyboard.shift` |
| A | `keyboard.a` |
| D | `keyboard.d` |
| W | `keyboard.w` |
| S | `keyboard.s` |
| J | `keyboard.j` |
| K | `keyboard.k` |
| E | `keyboard.e` |
| R | `keyboard.r` |

## Mouse Names

| Mouse input | Code |
| --- | --- |
| Left button | `mouse.left` |
| Right button | `mouse.right` |
| Middle button | `mouse.middle` |
| Mouse x position | `mouse.x` |
| Mouse y position | `mouse.y` |
| Mouse position pair | `mouse.position` |

## Challenge Ideas

- Make `A` and `D` move the player instead of arrow keys.
- Make `Shift` sprint.
- Make the mouse left button attack.
- Make the player jump lower if they are holding Down.
- Make controls reverse while a custom condition is true.
