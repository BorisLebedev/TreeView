from PyQt5.QtWidgets import QSizePolicy
from PyQt5.QtWidgets import QPlainTextEdit


class PlainTextResizable(QPlainTextEdit):
    def __init__(self) -> None:
        super().__init__()
        self.initSettings()
        self.textChanged.connect(self.resizeSentence)

    def initSettings(self) -> None:
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)
        self.min_height = 20
        self.current_height = 0
        self.fontSize = self.document().defaultFont().pointSize()
        self.min_height = self.fontSize

    def resizeSentence(self) -> None:
        self.setFixedHeight(self.min_height)
        self.setFixedHeight(self.height() + 1)
        while self.verticalScrollBar().isVisible() and self.height() < 1000:
            self.setFixedHeight(self.height() + self.fontSize)
