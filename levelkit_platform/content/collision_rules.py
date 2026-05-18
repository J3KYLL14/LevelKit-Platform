"""Student-programmed collision outcomes.

The engine detects when rectangles touch. These functions decide what should
happen after the collision is detected.
"""


def player_hits_hazard(game, player, hazard):
    game.damage_player(1)


def player_reaches_checkpoint(game, player, checkpoint):
    game.set_checkpoint(checkpoint)


def player_collects_pickup(game, player, pickup):
    game.collect_pickup(pickup)


def player_talks_to_npc(game, player, npc):
    game.say(game.dialogue[npc.dialogue_id], speaker=npc.name)


def player_reaches_win_zone(game, player, win_zone):
    game.win()


def player_hits_exit(game, player, exit_zone):
    game.go_to(exit_zone.target_level, exit_zone.target_spawn)
