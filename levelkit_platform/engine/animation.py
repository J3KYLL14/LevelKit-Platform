class AnimationState:
    """Tiny animation helper based on named states and frame timing."""

    def __init__(self, default="idle"):
        self.state = default
        self.timer = 0.0
        self.frame = 0

    def set(self, state):
        if state != self.state:
            self.state = state
            self.timer = 0.0
            self.frame = 0

    def update(self, dt, frame_time=0.12, frame_count=2):
        self.timer += dt
        if self.timer >= frame_time:
            self.timer = 0.0
            self.frame = (self.frame + 1) % frame_count
