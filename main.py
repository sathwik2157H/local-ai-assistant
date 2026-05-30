import sys

from PyQt6.QtWidgets import QApplication

from app.ui.orb_widget import OrbWidget
from app.core.state_manager import StateManager
from app.core.state import AssistantState

from PyQt6.QtCore import QTimer
from app.core.state import AssistantState


def main():
    app = QApplication(sys.argv)

    state_manager = StateManager()

    window = OrbWidget(state_manager)

    window.show()

    states = [
        AssistantState.IDLE,
        AssistantState.LISTENING,
        AssistantState.THINKING,
        AssistantState.SPEAKING,
        AssistantState.ERROR
    ]

    index = {"value": 0}

    def cycle_states():
        state_manager.set_state(
            states[index["value"]]
        )

        print(
            f"State Changed -> {states[index['value']].value}"
        )

        index["value"] = (
            index["value"] + 1
        ) % len(states)

    timer = QTimer()

    timer.timeout.connect(
        cycle_states
    )

    timer.start(3000)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()