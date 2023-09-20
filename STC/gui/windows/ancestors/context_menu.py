""" Родительские классы для контекстных меню """
from PyQt5.QtWidgets import QAction
from PyQt5.QtWidgets import QMenu


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

    def initBasicActions(self):
        """ Вызов методов создания элементов для меню """

        self.addAction(self.actionAddRow())
        self.addAction(self.actionCopyRow())
        self.addAction(self.actionDelRow())

    def initActionText(self) -> None:
        """ Текст элементов контекстного меню """

        self.del_action_text = 'Удалить строку'
        self.add_action_text = 'Добавить строку'
        self.copy_action_text = 'Скопировать строку'

    def actionCopyRow(self) -> QAction:
        """ Действие копирования выбранной строки """

        action = QAction(self.object)
        action.setText(self.copy_action_text)
        action.triggered.connect(self.object.copyRow)
        return action
