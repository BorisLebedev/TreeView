""" Окно поиска по тексту в данных иерархического древе """

from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt5.QtCore import Qt
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QTableView

from STC.gui.windows.ancestors.window import WindowBasic

if TYPE_CHECKING:
    from STC.gui.windows.hierarchy_find.model import StandartModelSearch


class WindowSearchTreeView(WindowBasic):
    """ Окно поиска по столбцам иерархической таблицы """

    findData = pyqtSignal()

    def __init__(self) -> None:
        self.line = QLineEdit()
        self.model = None
        self.table = None
        self.label = None
        super().__init__()
        self.title = "Поиск"
        self.initUI()
        self.line.setFocus()

    def initUI(self) -> None:
        """ Внешний вид и размер окна """

        self.setWindowFlags(Qt.CustomizeWindowHint)
        self.basic_layout.itemAt(0).widget().layout.itemAt(0).widget().setText(self.title)
        self.basic_layout.itemAt(0).widget().layout.itemAt(1).widget().setHidden(True)
        self.basic_layout.itemAt(0).widget().layout.itemAt(2).widget().setHidden(True)
        self.setGeometry(200, 200, 500, 100)
        self.setMinimumSize(500, 100)
        self.setMaximumSize(1980, 800)
        self.widgets()

    def widgets(self) -> None:
        """ Инициализация виджетов окна """

        label = QLabel('Найти')
        self.line = QLineEdit('')

        button_search = QPushButton('Найти')
        self.main_layout.addWidget(label, 0, 0)
        self.main_layout.addWidget(self.line, 0, 1)
        self.main_layout.addWidget(button_search, 1, 0, 1, 2)
        button_search.clicked.connect(self.findData)

    def showSearchResults(self, model: StandartModelSearch) -> None:
        """ Выводит результат поиска """

        self.model = model
        if model.rowCount() == 0:
            self.label = QLabel('Не найдено')
            self.main_layout.addWidget(self.label, 2, 0, 1, 2)
            self.resize(500, 150)
        else:
            self.drawTableView()

    def windowSizeAdjustment(self) -> None:
        """ Изменяет размер окна поиска """

        self.table.setSortingEnabled(True)
        for column in range(self.table.horizontalHeader().count()):
            self.table.resizeColumnToContents(column)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.resize(70 + self.table.horizontalHeader().length(),
                    120 + self.table.verticalHeader().length() +
                    self.table.horizontalHeader().height())

    def drawTableView(self) -> None:
        """ Представление для модели найденных данных.
            Таблица с текстом ячеек и ссылкой на строку
            в иерархическом представлении """

        self.table = QTableView()
        self.table.setModel(self.model)
        self.main_layout.addWidget(self.table, 2, 0, 1, 2)
        self.table.clicked.connect(lambda: self.model.selectionChanged(self.table.currentIndex()))
        self.table.setColumnHidden(0, True)
        self.windowSizeAdjustment()
