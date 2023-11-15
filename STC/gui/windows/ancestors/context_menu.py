""" Родительские классы для контекстных меню """
from PyQt5.QtWidgets import QAction
from PyQt5.QtWidgets import QMenu
from PyQt5.Qt import QColor
from PyQt5.QtGui import QPixmap
from PyQt5.QtGui import QIcon
from PyQt5.QtGui import QKeySequence
from PyQt5 import Qt


# Базовое контекстное меню
class ContextMenu(QMenu):
    """ Родительский класс для всех контекстных меню """

    def __init__(self, obj) -> None:
        super().__init__()
        self.object = obj


# Контекстное меню для базовой таблицы
class ContextMenuForBasicTable(ContextMenu):
    """ Родительский класс для контекстных меню в таблицах
        Функции:
        1. Добавить строку
        2. Удалить строку
    """

    def __init__(self, obj) -> None:
        super().__init__(obj)
        self.initActionText()
        self.initBasicActions()

    def initBasicActions(self):
        """ Вызов методов создания элементов для меню """

        self.addAction(self.actionDelRow())
        self.addAction(self.actionAddRow())

    def initActionText(self) -> None:
        """ Текст элементов контекстного меню """

        self.del_action_text = 'Удалить строку'
        self.add_action_text = 'Добавить строку'

    def actionDelRow(self) -> QAction:
        """ Действие удаления строки таблицы """

        action = QAction(self.object)
        action.setText(self.del_action_text)
        action.triggered.connect(self.object.deleteRow)
        return action

    def actionAddRow(self) -> QAction:
        """ Действие добавления строки таблицы """

        action = QAction(self.object)
        action.setText(self.add_action_text)
        action.triggered.connect(self.object.addNewRow)
        return action


# Контекстное меню для базовой таблицы
class ContextMenuForSpecProductsTable(ContextMenuForBasicTable):
    """ Родительское меню для таблицы с копированием строки
        Функции:
        1. Добавить строку
        2. Удалить строку
        3. Скопировать строку
    """

    def __init__(self, obj):
        super().__init__(obj)

    def initBasicActions(self):
        """ Вызов методов создания элементов для меню """

        self.addAction(self.actionAddRow())
        self.addAction(self.actionCopyRow())
        self.addAction(self.actionDelRows())
        # self.addAction(self.actionDelRow())
        self.addAction(self.actionMark())
        self.addAction(self.actionDelMark())

    def initActionText(self) -> None:
        """ Текст элементов контекстного меню """

        self.del_action_text = 'Удалить строку'
        self.add_action_text = 'Добавить строку'
        self.copy_action_text = 'Скопировать строку'
        self.mark_action_text = 'Выделить цветом'
        self.del_mark_action_text = 'Убрать выделение'
        self.del_all_action_text = 'Удалить строки'

    def actionCopyRow(self) -> QAction:
        """ Действие копирования выбранной строки """

        action = QAction(self.object)
        action.setText(self.copy_action_text)
        action.triggered.connect(self.object.copyRow)
        return action

    def actionMark(self) -> QAction:
        """ Действие выделение цветом выбранной строки """

        action = QAction(self.object)
        action.setText(self.mark_action_text)
        action.triggered.connect(self.object.markRows)
        return action

    def actionDelMark(self) -> QAction:
        """ Действие убрать выделение цветом выбранной строки """

        action = QAction(self.object)
        action.setText(self.del_mark_action_text)
        action.triggered.connect(self.object.markRowsDel)
        return action

    def actionDelRows(self) -> QAction:
        """ Действие убрать выделение цветом выбранной строки """

        action = QAction(self.object)
        action.setText(self.del_all_action_text)
        action.triggered.connect(self.object.deleteRows)
        return action