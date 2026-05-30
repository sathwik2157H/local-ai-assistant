from app.core.state import AssistantState


class StateManager:
    def __init__(self):
        self.current_state = AssistantState.IDLE

    def get_state(self):
        return self.current_state

    def set_state(self, state):
        self.current_state = state