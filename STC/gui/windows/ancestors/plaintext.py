""" Переопределение Qt класса QPlainTextEdit """

from PyQt5.QtWidgets import QSizePolicy
from PyQt5.QtWidgets import QPlainTextEdit


class PlainTextResizable(QPlainTextEdit):
    """ QPlainTextEdit с предустановками геометрии и
        изменением размеров при печати текста в нем"""

    def __init__(self) -> None:
        super().__init__()
        self.initSettings()
        self.textChanged.connect(self.resizeSentence)

    def initSettings(self) -> None:
        """ Настройки геометрии виджета """

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)
        self.min_height = 20
        self.current_height = 0
        self.font_size = self.document().defaultFont().pointSize()
        self.min_height = self.font_size

    def resizeSentence(self) -> None:
        """ Изменение размера при вписывании текста """

        self.setFixedHeight(self.min_height)
        self.setFixedHeight(self.height() + 1)
        while self.verticalScrollBar().isVisible() and self.height() < 1000:
            self.setFixedHeight(self.height() + self.font_size)
