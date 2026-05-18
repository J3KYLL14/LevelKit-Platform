"""Student-programmed player controls.

The engine still handles gravity, collision detection, and collision response.
This file controls what the player tries to do when keys or mouse buttons are
pressed.
"""


def control_player(player, keyboard, mouse, dt):
    actions = {
        "melee": False,
        "shoot": False,
    }

    player.velocity.x = 0

    if keyboard.left:
        player.velocity.x = -player.speed
        player.facing = -1

    if keyboard.right:
        player.velocity.x = player.speed
        player.facing = 1

    if keyboard.shift:
        player.velocity.x *= 1.5

    if keyboard.space and player.grounded:
        player.velocity.y = -player.jump_power
        player.grounded = False

    if keyboard.j or mouse.left:
        actions["melee"] = True

    if keyboard.k or mouse.right:
        actions["shoot"] = True

    return actions
