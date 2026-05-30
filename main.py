import sys

from PyQt6.QtWidgets import QApplication

from app.ui.orb_widget import OrbWidget


def main():
    app = QApplication(sys.argv)

    window = OrbWidget()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()