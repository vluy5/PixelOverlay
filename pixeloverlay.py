# pixeloverlay.py# Pixel Overlay Application
# This application allows users to overlay an image on their screen with adjustable opacity
# Mei dev 2025 TG: meiloli
import sys
import os
import json
from PyQt5 import QtWidgets, QtGui, QtCore


class Overlay(QtWidgets.QWidget):
    def __init__(self, image_path):
        super().__init__()
        self.setWindowFlags(
            QtCore.Qt.FramelessWindowHint |
            QtCore.Qt.WindowStaysOnTopHint |
            QtCore.Qt.Tool |
            QtCore.Qt.WindowTransparentForInput
        )
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)

        self.image_path = image_path
        self.pixmap = QtGui.QPixmap(image_path)
        self.scale_factor = 1.0
        self.offset = QtCore.QPoint(0, 0)
        self.opacity = 0.5

        self.control_panel = DraggablePanel(self)
        self.control_panel.show()

        self.resize(self.pixmap.size())

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setOpacity(self.opacity)
        scaled = self.pixmap.scaled(
            int(self.pixmap.width() * self.scale_factor),
            int(self.pixmap.height() * self.scale_factor),
            QtCore.Qt.KeepAspectRatio,
            QtCore.Qt.SmoothTransformation
        )
        painter.drawPixmap(self.offset, scaled)

    def save_config(self):
        config = {
            "offset": {"x": self.offset.x(), "y": self.offset.y()},
            "scale_factor": self.scale_factor,
            "opacity": self.opacity
        }
        base_name = os.path.basename(self.image_path)
        config_name = f"config_{base_name}.json"
        with open(config_name, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
        QtWidgets.QMessageBox.information(self, "Saved", f"Config saved in {config_name}")

    def load_config(self, config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        self.offset = QtCore.QPoint(config["offset"]["x"], config["offset"]["y"])
        self.scale_factor = config["scale_factor"]
        self.opacity = config["opacity"]
        self.control_panel.inner.opacity_slider.setValue(int(self.opacity * 100))
        self.update()


class DraggablePanel(QtWidgets.QWidget):
    def __init__(self, overlay):
        super().__init__()
        self.overlay = overlay
        self.setWindowFlags(
            QtCore.Qt.FramelessWindowHint |
            QtCore.Qt.WindowStaysOnTopHint |
            QtCore.Qt.Tool
        )
        self.setStyleSheet("background-color: transparent;")

        self.inner = ControlPanel(self.overlay, self)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.addWidget(self.inner)

        self.drag_position = None
        screen = QtWidgets.QApplication.primaryScreen().availableGeometry()
        self.move(screen.width() - 220, (screen.height() - self.height()) // 2)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            if not self.inner.geometry().contains(event.pos()):
                self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
                event.accept()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() == QtCore.Qt.LeftButton and self.drag_position:
            self.move(event.globalPos() - self.drag_position)
            event.accept()
        super().mouseMoveEvent(event)


class ControlPanel(QtWidgets.QWidget):
    def __init__(self, overlay, parent=None):
        super().__init__(parent)
        self.overlay = overlay
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(30,30,30,200);
                color: white;
                border: 2px solid #888;
                border-radius: 6px;
            }
            QPushButton {
                background-color: rgba(60,60,60,200);
                border: none;
                padding: 5px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: rgba(90,90,90,200);
            }
        """)

        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)

        up_btn = QtWidgets.QPushButton("↑")
        down_btn = QtWidgets.QPushButton("↓")
        left_btn = QtWidgets.QPushButton("←")
        right_btn = QtWidgets.QPushButton("→")
        zoom_in_btn = QtWidgets.QPushButton("Zoom In")
        zoom_out_btn = QtWidgets.QPushButton("Zoom Out")

        opacity_label = QtWidgets.QLabel("Opacity")
        opacity_label.setAlignment(QtCore.Qt.AlignCenter)
        self.opacity_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.opacity_slider.setRange(0, 100)
        self.opacity_slider.setValue(int(self.overlay.opacity * 100))
        self.opacity_slider.valueChanged.connect(self.change_opacity)

        save_btn = QtWidgets.QPushButton("Create Config")
        load_btn = QtWidgets.QPushButton("Load Config")
        close_btn = QtWidgets.QPushButton("Close")

        layout.addWidget(up_btn)
        layout.addWidget(down_btn)
        layout.addWidget(left_btn)
        layout.addWidget(right_btn)
        layout.addWidget(zoom_in_btn)
        layout.addWidget(zoom_out_btn)
        layout.addWidget(opacity_label)
        layout.addWidget(self.opacity_slider)
        layout.addWidget(save_btn)
        layout.addWidget(load_btn)
        layout.addWidget(close_btn)
        self.setLayout(layout)

        up_btn.clicked.connect(lambda: self.move_overlay(0, -10))
        down_btn.clicked.connect(lambda: self.move_overlay(0, 10))
        left_btn.clicked.connect(lambda: self.move_overlay(-10, 0))
        right_btn.clicked.connect(lambda: self.move_overlay(10, 0))
        zoom_in_btn.clicked.connect(lambda: self.zoom(1.1))
        zoom_out_btn.clicked.connect(lambda: self.zoom(0.9))
        save_btn.clicked.connect(self.overlay.save_config)
        load_btn.clicked.connect(self.load_config_dialog)
        close_btn.clicked.connect(QtWidgets.qApp.quit)

    def move_overlay(self, dx, dy):
        self.overlay.offset += QtCore.QPoint(dx, dy)
        self.overlay.update()

    def zoom(self, factor):
        self.overlay.scale_factor *= factor
        self.overlay.update()

    def change_opacity(self, value):
        self.overlay.opacity = value / 100.0
        self.overlay.update()

    def load_config_dialog(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Select Config", "", "JSON files (*.json)"
        )
        if path:
            self.overlay.load_config(path)


def main():
    app = QtWidgets.QApplication(sys.argv)
    path, _ = QtWidgets.QFileDialog.getOpenFileName(
        None, "Select Image", "", "Images (*.png *.jpg *.jpeg *.bmp)"
    )
    if not path:
        print("File not selected")
        return
    overlay = Overlay(path)
    overlay.showFullScreen()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
