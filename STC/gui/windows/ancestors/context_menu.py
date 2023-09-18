from PyQt5.QtWidgets import QAction
from PyQt5.QtWidgets import QMenu


# Базовое контекстное меню
class ContextMenu(QMenu):

    def __init__(self, obj) -> None:
        super().__init__()
        self.object = obj


# Контекстное меню для базовой таблицы
class ContextMenuForBasicTable(ContextMenu):

    def __init__(self, obj) -> None:
        super().__init__(obj)
        self.initActionText()
        self.initBasicActions()

    def initBasicActions(self):
        self.addAction(self.actionDelRow())
        self.addAction(self.actionAddRow())

    def initActionText(self) -> None:
        self.del_action_text = 'Удалить строку'
        self.add_action_text = 'Добавить строку'

    def actionDelRow(self) -> QAction:
        action = QAction(self.object)
        action.setText(self.del_action_text)
        action.triggered.connect(lambda: self.object.deleteRow())
        return action

    def actionAddRow(self) -> QAction:
        action = QAction(self.object)
        action.setText(self.add_action_text)
        action.triggered.connect(lambda: self.object.addNewRow())
        return action


# Контекстное меню для базовой таблицы
class ContextMenuForSpecProductsTable(ContextMenuForBasicTable):

    def __init__(self, obj) -> None:
        super().__init__(obj)

    def initBasicActions(self):
        self.addAction(self.actionAddRow())
        self.addAction(self.actionCopyRow())
        self.addAction(self.actionDelRow())

    def initActionText(self) -> None:
        self.del_action_text = 'Удалить строку'
        self.add_action_text = 'Добавить строку'
        self.copy_action_text = 'Скопировать строку'

    def actionCopyRow(self) -> QAction:
        action = QAction(self.object)
        action.setText(self.copy_action_text)
        action.triggered.connect(lambda: self.object.copyRow())
        return action
