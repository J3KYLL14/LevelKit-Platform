# 04 Make A Pickup

Create or edit a file in:

```text
levelkit_platform/content/items/
```

Quest item:

```python
from levelkit import quest_item


ITEMS = [
    quest_item("Sun Orb", id="sun_orb"),
]
```

Healing item:

```python
from levelkit import healing_item


ITEMS = [
    healing_item("Healing Berry", id="berry", heals=1),
]
```

Then place the pickup in the visual level builder.
