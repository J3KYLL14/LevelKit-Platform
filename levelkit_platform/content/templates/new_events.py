from levelkit import when_enter_level, when_pickup


when_enter_level("meadow", say="This message appears when the player enters the meadow.")
when_pickup("sun_orb", say="This message appears when the player collects the Sun Orb.")
