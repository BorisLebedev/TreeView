from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from STC.product.product import Operation
    from STC.product.product import Sentence
    from STC.gui.windows.document_generator.frame import FrameOperationText

from PyQt5.QtCore import QPoint
from PyQt5.QtCore import Qt
from PyQt5.QtCore import pyqtSignal
from STC.gui.windows.ancestors.plaintext import PlainTextResizable
from STC.gui.windows.document_generator.context_menu import ContextMenuForSentence


# Виджет для хранения перехода в таблице переходов операции
class SentenceTextEdit(PlainTextResizable):
    sentenceTextChanged = pyqtSignal()

    def __init__(self, sentence: Sentence, frame: FrameOperationText) -> None:
        super().__init__()
        self.sentence = sentence
        self.setPlainText(self.sentence.text)
        self.frame = frame
        self.updateGeometry()
        self.textChanged.connect(self.sentenceTextChanged)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.showContextMenu)

    def showContextMenu(self, point: QPoint) -> None:
        self.context_menu = ContextMenuForSentence(self)
        qp = self.sender().mapToGlobal(point)
        self.context_menu.exec_(qp)

    @property
    def current_height(self) -> int:
        return self.height()

    @current_height.setter
    def current_height(self, value: int) -> None:
        self.setFixedHeight(value)


# Виджет с текстом ИОТ, оснастки и других дополнительных данных генерируемой МК
class PlainText(PlainTextResizable):
    def __init__(self, operation: Operation) -> None:
        super(PlainText, self).__init__()
        self.operation = operation
        self.upd()

    def updateGeometry(self) -> None:
        self.resizeSentence()

    def upd(self) -> None:
        return None


# Виджет отображающих список ИОТ операции
class IotText(PlainText):

    def upd(self) -> None:
        self.setPlainText(self.operation.iot)


# Виджет отображающих список оснастки операции
class RigText(PlainText):

    def upd(self) -> None:
        self.setPlainText(self.operation.rig)


# Виджет отображающих список оборудования операции
class EquipmentText(PlainText):

    def upd(self) -> None:
        self.setPlainText(self.operation.equipment)


# Виджет отображающих список материалов операции
class MatText(PlainText):

    def upd(self) -> None:
        self.setPlainText(self.operation.mat)
        # self.textChanged.emit()


# Виджет отображающих список документов операции
class DocText(PlainText):

    def upd(self) -> None:
        self.setPlainText(self.operation.documents_text)
