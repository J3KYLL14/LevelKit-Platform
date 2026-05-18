# 06 Add Sprites

Put image files in:

```text
levelkit_platform/content/assets/sprites/
```

Then choose them in the visual level builder, or set a default sprite in code:

```python
from levelkit import enemy


CHARACTER = enemy(
    "Forest Slime",
    id="forest_slime",
    sprite="sprites/forest_slime.png",
)
```

Animation spritesheets can be added with animation dictionaries once students are ready for advanced work.
