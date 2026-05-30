import sys
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QPainter, QColor


class AIAssistantWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.drag_pos = QPoint()

        self.setWindowTitle("Nova")

        self.setFixedSize(120, 180)

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        painter.setBrush(QColor(0, 170, 255, 220))
        painter.setPen(Qt.PenStyle.NoPen)

        painter.drawEllipse(20, 20, 140, 140)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            delta = event.globalPosition().toPoint() - self.drag_pos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.drag_pos = event.globalPosition().toPoint()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = AIAssistantWindow()
    window.show()

    sys.exit(app.exec())