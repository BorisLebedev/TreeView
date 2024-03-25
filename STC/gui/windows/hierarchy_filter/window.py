""" Окно фильтра иерархической таблицы """

from __future__ import annotations

from typing import TYPE_CHECKING

import logging

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QTableView

from STC.gui.windows.ancestors.window import WindowBasic
from STC.gui.windows.hierarchy_filter.frame import TableViewFilter


if TYPE_CHECKING:
    from PyQt5.Qt import QPoint
    from STC.gui.windows.ancestors.model import SortFilterProxyModel


class WindowFilter(WindowBasic):
    """ Окно фильтра иерархической таблицы
        Представление реализовано как стандартный QTableView,
        а не переопределено как HierarchicalView """

    def __init__(self, model: SortFilterProxyModel) -> None:
        super().__init__()
        self.title = "Результат фильтра"
        self.base_model = model
        self.table = None
        self.total = self.base_model.rowCount()
        self.initUI()

    def initUI(self) -> None:
        """ Настройка внешнего вида окна """

        self.setWindowFlags(Qt.CustomizeWindowHint)
        self.basic_layout.itemAt(0).widget().layout.itemAt(0).widget().setText(self.title)
        self.setGeometry(200, 200, 500, 100)
        self.setMinimumSize(500, 100)
        self.widgets()
        self.setFilterMenu()
        self.updStatusBar()

    def widgets(self) -> None:
        """ Виджеты окна """

        self.table = QTableView()
        self.table.setModel(self.base_model)
        # self.initDelegates()
        self.main_layout.addWidget(self.table, 0, 0)
        self.table.clicked.connect(
            lambda: self.table.model().selectionChanged(self.table.currentIndex()))
        self.table.setColumnHidden(0, True)
        self.table.horizontalHeader().setSectionsMovable(True)
        self.windowSizeAdjustment()

    def initDelegates(self) -> None:
        """ Инициализация делегатов для представления модели """

        for column in range(self.table.model().columnCount()):
            delegate = self.base_model.tree_view.itemDelegateForColumn(column)
            self.table.setItemDelegateForColumn(column, delegate)

    def setFilterMenu(self) -> None:
        """ Окно фильтрации данных в качестве контекстного меню """

        self.table.horizontalHeader().setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.horizontalHeader().customContextMenuRequested.connect(self.showFilterMenu)

    def showFilterMenu(self, point: QPoint) -> None:
        """ Окно фильтрации данных для определенного столбца """

        logging.debug(self.base_model)
        logical_index = self.table.horizontalHeader().logicalIndexAt(point)
        TableViewFilter(window=self, logical_index=logical_index)

    def windowSizeAdjustment(self) -> None:
        """ Настройка размеров окна и столбцов таблицы """

        self.table.setSortingEnabled(True)
        for column in range(self.table.horizontalHeader().count()):
            self.table.resizeColumnToContents(column)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.resizeRowsToContents()
        self.resize(
            100 + self.table.verticalHeader().width() + self.table.horizontalHeader().length(),
            120 + self.table.verticalHeader().length() + self.table.horizontalHeader().height())

    def updStatusBar(self) -> None:
        """ Изменение текста статусбара окна """

        find = self.table.model().rowCount()
        percent = int(find/self.total*100)
        msg = f'Найдено: {find} из {self.total}. {percent}% от общего количества.'
        self.main_window.statusBar().showMessage(f'{msg}')
