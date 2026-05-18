# 05 Add Dialogue

Dialogue files live in:

```text
levelkit_platform/content/dialogue/
```

Example:

```python
DIALOGUES = {
    "guide_intro": "Welcome to the meadow!",
}
```

NPCs use `dialogue_id` to choose what they say:

```python
from levelkit import npc


CHARACTER = npc(
    "Guide",
    id="guide_npc",
    dialogue_id="guide_intro",
)
```
