from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PyQt5.Qt import QResizeEvent
    from PyQt5.Qt import QMouseEvent

from PyQt5.QtCore import QPoint
from PyQt5.QtCore import Qt
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QCloseEvent
from PyQt5.QtWidgets import QFrame
from PyQt5.QtWidgets import QGridLayout
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QWidget

from STC.config.config import CONFIG


# Верхняя планка базового окна (WindowBasic)
class CustomBar(QWidget):

    def __init__(self, parent: WindowBasic) -> None:
        super(CustomBar, self).__init__(parent)
        self.parent = parent
        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.title = QLabel("Title")
        btn_size = 20

        self.btn_close = QPushButton()
        self.btn_close.setIcon(CONFIG.style.close)
        self.btn_close.clicked.connect(self.btnCloseClicked)
        self.btn_close.setFixedSize(btn_size, btn_size)

        self.btn_min = QPushButton()
        self.btn_min.setIcon(CONFIG.style.underline)
        self.btn_min.clicked.connect(self.btnMinClicked)
        self.btn_min.setFixedSize(btn_size, btn_size)

        self.btn_max = QPushButton()
        self.btn_max.setIcon(CONFIG.style.full_screen)
        self.btn_max.clicked.connect(self.btnMaxClicked)
        self.btn_max.setFixedSize(btn_size, btn_size)

        self.title.setFixedHeight(btn_size)
        self.title.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.title)
        self.layout.addWidget(self.btn_min)
        self.layout.addWidget(self.btn_max)
        self.layout.addWidget(self.btn_close)
        self.customStyle()
        self.setLayout(self.layout)
        self.start = QPoint(0, 0)
        self.pressing = False

    def resizeEvent(self, event: QResizeEvent) -> None:
        super(CustomBar, self).resizeEvent(event)
        self.title.setFixedWidth(self.parent.width())

    def mousePressEvent(self, event: QMouseEvent) -> None:
        self.start = self.mapToGlobal(event.pos())
        self.pressing = True

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self.pressing:
            self.end = self.mapToGlobal(event.pos())
            self.movement = self.end - self.start
            self.parent.setGeometry(self.mapToGlobal(self.movement).x(),
                                    self.mapToGlobal(self.movement).y(),
                                    self.parent.width(),
                                    self.parent.height())
            self.start = self.end

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self.pressing = False

    def btnCloseClicked(self) -> None:
        self.parent.close()

    def btnMaxClicked(self) -> None:
        if self.parent.isMaximized():
            self.parent.showNormal()
            self.btn_max.setIcon(CONFIG.style.full_screen)
        else:
            self.parent.showMaximized()
            self.btn_max.setIcon(CONFIG.style.exit_full_screen)

    def btnMinClicked(self) -> None:
        self.parent.showMinimized()

    def customStyle(self):
        self.btn_close.setStyleSheet(CONFIG.style.bar_btn_style_str)
        self.btn_min.setStyleSheet(CONFIG.style.bar_btn_style_str)
        self.btn_max.setStyleSheet(CONFIG.style.bar_btn_style_str)
        self.title.setStyleSheet(CONFIG.style.bar_title_style_str)


# Базовый класс окна с основными настройками
class WindowBasic(QWidget):

    closeWindow = pyqtSignal(list)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.bar = CustomBar(self)
        self.main_window = QMainWindow()

        self.basic_layout = QVBoxLayout()
        self.setLayout(self.basic_layout)

        self.basic_layout.addWidget(self.bar)
        self.basic_layout.addWidget(self.main_window)

        self.basic_layout.setContentsMargins(0, 0, 0, 0)
        self.basic_layout.setAlignment(Qt.AlignTop)
        self.setMinimumSize(10, 10)
        self.setWindowFlags(Qt.FramelessWindowHint)

        self.main_frame = QFrame()
        self.main_window.setCentralWidget(self.main_frame)
        self.main_layout = QGridLayout()
        self.main_frame.setLayout(self.main_layout)

    def closeEvent(self, event: QCloseEvent) -> None:
        self.closeWindow.emit([self])
