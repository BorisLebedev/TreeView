""" Виджеты многострочного текста для
    окна разработки маршрутных карт """

from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt5.QtCore import QPoint
from PyQt5.QtCore import Qt
from PyQt5.QtCore import pyqtSignal
from STC.gui.windows.ancestors.plaintext import PlainTextResizable
from STC.gui.windows.document_generator.context_menu import ContextMenuForSentence

if TYPE_CHECKING:
    from STC.product.product import Operation
    from STC.product.product import Sentence
    from STC.gui.windows.document_generator.frame import FrameOperationText


class SentenceTextEdit(PlainTextResizable):
    """ Виджет для хранения перехода в
        таблице переходов операции """

    sentenceTextChanged = pyqtSignal()

    def __init__(self, sentence: Sentence, frame: FrameOperationText) -> None:
        self.context_menu = None
        super().__init__()
        self.sentence = sentence
        self.setPlainText(self.sentence.text)
        self.frame = frame
        self.updateGeometry()
        self.textChanged.connect(self.sentenceTextChanged)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.showContextMenu)

    def showContextMenu(self, point: QPoint) -> None:
        """ Контекстное меню """

        self.context_menu = ContextMenuForSentence(self)
        qpoint = self.sender().mapToGlobal(point)
        self.context_menu.exec_(qpoint)

    @property
    def current_height(self) -> int:
        """ Возвращает текущую высоту виджета """

        return self.height()

    @current_height.setter
    def current_height(self, value: int) -> None:
        """ Устанавливает текущую высоту виджета"""

        self.setFixedHeight(value)


class PlainText(PlainTextResizable):
    """ Родительский класс виджетов с текстом ИОТ, оснастки
        и других дополнительных данных генерируемой МК """

    def __init__(self, operation: Operation) -> None:
        super().__init__()
        self.setReadOnly(True)
        self.operation = operation
        self.upd()

    def updateGeometry(self) -> None:
        """ Переопределение метода изменения размера """

        self.resizeSentence()

    def upd(self) -> None:
        """ Обновление виджета
            (изменение текста) """

        return None


class IotText(PlainText):
    """ Виджет отображающих список ИОТ операции """

    def upd(self) -> None:
        """ Обновление виджета
            (изменение текста) """

        self.setPlainText(self.operation.iot)


class RigText(PlainText):
    """ Виджет отображающих список оснастки операции """

    def upd(self) -> None:
        """ Обновление виджета
            (изменение текста) """

        self.setPlainText(self.operation.rig)


class EquipmentText(PlainText):
    """ Виджет отображающих список оборудования операции """

    def upd(self) -> None:
        """ Обновление виджета
            (изменение текста) """

        self.setPlainText(self.operation.equipment)


class MatText(PlainText):
    """ Виджет отображающих список материалов операции """

    def upd(self) -> None:
        """ Обновление виджета
            (изменение текста) """

        self.setPlainText(self.operation.mat)
        # self.textChanged.emit()


class DocText(PlainText):
    """ Виджет отображающих список документов операции """

    def upd(self) -> None:
        """ Обновление виджета
            (изменение текста) """

        self.setPlainText(self.operation.documents_text)
