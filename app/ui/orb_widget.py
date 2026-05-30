from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QPoint, QTimer
from PyQt6.QtGui import QPainter, QColor
from math import sin
from PyQt6.QtGui import QColor


class OrbWidget(QWidget):
    def __init__(self, state_manager):
        super().__init__()
        self.state_manager = state_manager

        self.current_color = QColor(0, 170, 255)

        self.target_colors = {
            "idle": QColor(30, 144, 255),
            "listening": QColor(0, 255, 255),
            "thinking": QColor(170, 85, 255),
            "speaking": QColor(255, 200, 50),
            "error": QColor(255, 60, 60),
        }

        self.drag_pos = QPoint()

        self.base_size = 140
        self.pulse_size = 140

        self.t = 0
        self.breath_speed = 0.05
        self.breath_amplitude = 8

        self.setWindowTitle("Nova")

        self.setFixedSize(180, 180)

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.timer = QTimer()
        self.timer.timeout.connect(self.animate)
        self.timer.start(16)

    def animate(self):
        self.update_state_visuals()
        self.t += self.breath_speed

        self.pulse_size = (
            self.base_size
            + sin(self.t) * self.breath_amplitude
        )

        self.update()
    
    def update_state_visuals(self):
        state = self.state_manager.get_state().value

        target = self.target_colors[state]

        r = self.current_color.red()
        g = self.current_color.green()
        b = self.current_color.blue()

        r += (target.red() - r) * 0.08
        g += (target.green() - g) * 0.08
        b += (target.blue() - b) * 0.08

        self.current_color = QColor(
            int(r),
            int(g),
            int(b)
        )

    def paintEvent(self, event):
        painter = QPainter(self)

        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        painter.setBrush(
            QColor(
                self.current_color.red(),
                self.current_color.green(),
                self.current_color.blue(),
                220
            )
        )
        painter.setPen(Qt.PenStyle.NoPen)

        size = int(self.pulse_size)

        offset = (180 - size) // 2

        # Glow
        painter.setBrush(
            QColor(
                self.current_color.red(),
                self.current_color.green(),
                self.current_color.blue(),
                40
            )
        )

        glow_size = size + 20
        glow_offset = (180 - glow_size) // 2

        painter.drawEllipse(
            glow_offset,
            glow_offset,
            glow_size,
            glow_size
        )

        # Main orb
        painter.setBrush(
            QColor(
                self.current_color.red(),
                self.current_color.green(),
                self.current_color.blue(),
                220
            )
        )

        painter.drawEllipse(
            offset,
            offset,
            size,
            size
        )

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            delta = event.globalPosition().toPoint() - self.drag_pos

            self.move(
                self.x() + delta.x(),
                self.y() + delta.y()
            )

            self.drag_pos = event.globalPosition().toPoint()