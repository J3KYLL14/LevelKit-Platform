# 03 Make An Enemy

Create a new file in:

```text
levelkit_platform/content/characters/
```

Example:

```python
from levelkit import enemy


CHARACTER = enemy(
    "Forest Slime",
    id="forest_slime",
    health=2,
    speed="slow",
    touch_damage=1,
    patrol="short",
)
```

Beginner choices:

- `speed`: `still`, `slow`, `normal`, `fast`
- `patrol`: `none`, `short`, `long`

Then place the enemy in the visual level builder.
