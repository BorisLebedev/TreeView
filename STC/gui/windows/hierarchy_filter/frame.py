""" Окно с параметрами для фильтра данных """

from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt5.QtCore import QPoint
from PyQt5.QtCore import QRegExp
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QCheckBox
from PyQt5.QtWidgets import QComboBox
from PyQt5.QtWidgets import QFrame
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QScrollArea
from PyQt5.QtWidgets import QSizePolicy
from PyQt5.QtWidgets import QVBoxLayout
from STC.config.config import CONFIG

if TYPE_CHECKING:
    from STC.gui.windows.hierarchy_filter.window import WindowFilter


class TableViewFilter(QFrame):
    """ Меню фильтрации иерархических данных """

    # pylint: disable=too-many-instance-attributes

    def __init__(self, window: WindowFilter, logical_index: int) -> None:
        super().__init__(window)
        self.window = window
        self.table = window.table
        self.model = window.table.model()
        self.logical_index = logical_index
        self.proxyFilter()
        self.getData()
        self.setLayouts()
        self.setScrolls()
        self.setFrames()
        self.setCheckBoxes()
        self.setButtons()
        self.setComboBoxes()
        self.widgetRelation()
        self.filterPosition()
        self.filterGeometry()
        self.show()
        self.combobox.setFocus()
        self.setAutoFillBackground(True)

    def getData(self) -> None:
        """ Запрашивает уникальные значения столбца модели"""

        self.model.filters = self.proxy_filters
        self.model.invalidateFilter()
        self.data = self.model.getData(self.logical_index)

        self.model.filters = self.real_filters
        self.model.invalidateFilter()
        self.checked_data = self.model.getData(self.logical_index)

    def proxyFilter(self) -> None:
        """ Обеспечивает фильтрацию по нескольким столбцам """

        self.real_filters = self.model.filters
        self.proxy_filters = {}
        for key, regex in self.real_filters.items():
            if key != self.logical_index:
                self.proxy_filters[key] = regex

    def setLayouts(self) -> None:
        """ Инициализация параметров расположения виджетов """

        self.main_layout = QVBoxLayout()
        self.frame_layout = QVBoxLayout()

    def setScrolls(self) -> None:
        """ Инициализация области с возможностью прокрутки """

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)

    def setFrames(self) -> None:
        """ Инициализация рамок """

        self.frame = QFrame()

    def setCheckBoxes(self) -> None:
        """ Инициализация чекбоксов для уникальных данных """

        self.cb_inv = QCheckBox('Инвертировать')
        self.cb_inv.setChecked(True)
        self.cb_inv.stateChanged.connect(lambda: self.changeCbsState(_type='inv'))

        self.cb_all = QCheckBox('Выделить все')
        self.cb_all.setChecked(True)
        self.cb_all.stateChanged.connect(lambda: self.changeCbsState(_type='check_all'))

        self.cbs = {}
        sub_data = [item for item in self.data if item is not None]
        for data in sorted(sub_data):
            data = self.model.itemConversion(item=data)
            checkbox = QCheckBox(data)
            if data in self.checked_data:
                checkbox.setChecked(True)
            else:
                checkbox.setChecked(False)
            self.cbs[data] = checkbox

    def changeCbsState(self, _type: str) -> None:
        """ Изменение состояния чекбоксов выбора уникальных данных """

        for checkbox in self.cbs.values():
            if _type == 'inv':
                checkbox.setChecked(not checkbox.checkState())
            elif _type == 'check_all':
                checkbox.setChecked(self.cb_all.checkState())

    def setButtons(self) -> None:
        """ Инициализация кнопок """

        self.btn_ok = QPushButton('Ok')
        self.btn_ok.clicked.connect(self.filterApply)

        self.btn_cancel = QPushButton('Сбросить')
        self.btn_cancel.clicked.connect(self.filterReset)

        self.btn_close = QPushButton('Закрыть')
        self.btn_close.clicked.connect(self.close)

    def setComboBoxes(self) -> None:
        """ Инициализация комбобокса поиска по введенному тексту """

        self.combobox = QComboBox()
        self.combobox.setSizeAdjustPolicy(self.combobox.AdjustToMinimumContentsLengthWithIcon)
        self.combobox.setEditable(True)
        self.combobox.addItems(sorted(set(str(self.data))))
        self.combobox.setCurrentText('')

    def widgetRelation(self) -> None:
        """ Взаиморасположение виджетов """

        self.setLayout(self.main_layout)
        self.main_layout.addWidget(self.cb_all)
        self.main_layout.addWidget(self.cb_inv)
        self.main_layout.addWidget(self.combobox)
        self.main_layout.addWidget(self.scroll)
        self.scroll.setWidget(self.frame)
        self.main_layout.addWidget(self.btn_ok)
        self.main_layout.addWidget(self.btn_cancel)
        self.main_layout.addWidget(self.btn_close)
        self.frame.setLayout(self.frame_layout)
        for key in sorted(self.cbs.keys()):
            self.frame_layout.addWidget(self.cbs[key])

    def filterPosition(self) -> None:
        """ Расположение рамки параметров фильтрации
            данных относительно окна фильтра """

        point = QPoint(self.table.horizontalHeader().sectionViewportPosition(self.logical_index),
                       self.table.horizontalHeader().y())
        header_pos = self.table.horizontalHeader().mapTo(self.window, point)
        self.pos_x = header_pos.x()
        self.pos_y = header_pos.y() + self.table.horizontalHeader().height()

    def filterGeometry(self) -> None:
        """ Размер рамки параметров фильтрации
            данных относительно окна фильтра """

        self.setGeometry(self.pos_x, self.pos_y, self.table.columnWidth(self.logical_index), 0)
        self.setMinimumSize(self.table.columnWidth(self.logical_index), 0)
        self.setMaximumSize(200, 400)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.adjustSize()

    def filterReset(self) -> None:
        """ Сброс параметров фильтрации """

        self.model.filters = self.proxy_filters
        self.model.invalidateFilter()
        self.model.setHeaderData(self.logical_index,
                                 Qt.Horizontal,
                                 QIcon(None),
                                 Qt.DecorationRole)
        self.combobox.setCurrentText('')
        self.table.resizeRowsToContents()
        self.close()

    def filterApply(self) -> None:
        """ Применение фильтра к данным """

        if self.combobox.currentText() != '':
            regex_string = self.combobox.currentText()
            regex = QRegExp(f'{regex_string}')
            regex.setCaseSensitivity(Qt.CaseInsensitive)
        else:
            regex_data = []
            for cb_text, checkbox in self.cbs.items():
                if checkbox.isChecked():
                    regex_data.append(str(cb_text))
            regex_string = '|'.join(regex_data)
            regex = QRegExp(f'^({regex_string})$')

        self.model.filters[self.logical_index] = regex
        self.model.invalidateFilter()
        self.model.setHeaderData(self.logical_index,
                                 Qt.Horizontal,
                                 CONFIG.style.filter,
                                 Qt.DecorationRole)
        self.table.resizeRowsToContents()
        self.close()
        self.window.updStatusBar()
