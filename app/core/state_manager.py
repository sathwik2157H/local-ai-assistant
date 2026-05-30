from PyQt6.QtCore import QObject, pyqtSignal
from app.core.state import AssistantState


class StateManager(QObject):
    """
    Manages state transitions and notifies listeners.
    Acts as the single source of truth for the orb's current mode.
    """
    state_changed = pyqtSignal(AssistantState)

    def __init__(self):
        super().__init__()
        self._state = AssistantState.IDLE

    @property
    def state(self) -> AssistantState:
        return self._state

    def set_state(self, new_state: AssistantState):
        if new_state != self._state:
            self._state = new_state
            self.state_changed.emit(new_state)

    def cycle_next(self):
        """Cycle through all states — useful for testing."""
        states = list(AssistantState)
        idx = states.index(self._state)
        next_state = states[(idx + 1) % len(states)]
        self.set_state(next_state)
