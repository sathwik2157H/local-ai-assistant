"""
main.py — Entry point for the Orb Widget application.

Run with:
    python main.py

Controls:
    - Drag      : Move the orb anywhere on screen
    - Dbl-click : Cycle to next state manually
    The orb also auto-cycles every 3 seconds for demo purposes.
"""

import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from app.core.state_manager import StateManager
from app.ui.orb_widget import OrbWidget


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)

    state_manager = StateManager()
    orb = OrbWidget(state_manager)
    orb.show()

    # ── Demo: cycle through all states every 3 seconds ────────────────────────
    cycle_timer = QTimer()
    cycle_timer.timeout.connect(state_manager.cycle_next)
    cycle_timer.start(3000)  # 3000 ms = 3 seconds

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
