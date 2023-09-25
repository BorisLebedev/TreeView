""" Контекстные меню для окон администрирования БД """

from PyQt5.QtWidgets import QAction
from STC.gui.windows.ancestors.context_menu import ContextMenuForBasicTable


class ContextMenuForFrameAdminDef(ContextMenuForBasicTable):
    """ Родительский класс для контекстного меню таблицы
        администрирования данных """

    def __init__(self, obj):
        super().__init__(obj)
        self.addAction(self.copyRow())

    def copyRow(self) -> QAction:
        """ Опция копирования строки """

        action = QAction(self.object)
        action.setText("Копировать строку")
        action.triggered.connect(self.object.copyRow)
        return action
