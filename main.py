import sys

from PyQt6.QtWidgets import QApplication

from app.ui.orb_widget import OrbWidget
from app.core.state_manager import StateManager


def main():
    app = QApplication(sys.argv)

    state_manager = StateManager()

    window = OrbWidget(state_manager)

    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()