from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from STC.gui.windows.hierarchy_filter.window import WindowFilter

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


# Меню фильтрации иерархических данных
class TableViewFilter(QFrame):

    def __init__(self, window: WindowFilter, logicalIndex: int) -> None:
        super().__init__(window)
        self.window = window
        self.table = window.table
        self.model = window.table.model()
        self.logicalIndex = logicalIndex
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

    def getData(self) -> None:
        self.model.filters = self.proxy_filters
        self.model.invalidateFilter()
        self.data = self.model.getData(self.logicalIndex)

        self.model.filters = self.real_filters
        self.model.invalidateFilter()
        self.checked_data = self.model.getData(self.logicalIndex)

    def proxyFilter(self) -> None:
        self.real_filters = self.model.filters
        self.proxy_filters = {}
        for key, regex in self.real_filters.items():
            if key != self.logicalIndex:
                self.proxy_filters[key] = regex

    def setLayouts(self) -> None:
        self.main_layout = QVBoxLayout()
        self.frame_layout = QVBoxLayout()

    def setScrolls(self) -> None:
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)

    def setFrames(self) -> None:
        self.frame = QFrame()

    def setCheckBoxes(self) -> None:
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
            cb = QCheckBox(data)
            if data in self.checked_data:
                cb.setChecked(True)
            else:
                cb.setChecked(False)
            self.cbs[data] = cb

    def changeCbsState(self, _type: str) -> None:
        for cb in self.cbs.values():
            if _type == 'inv':
                cb.setChecked(not cb.checkState())
            elif _type == 'check_all':
                cb.setChecked(self.cb_all.checkState())

    def setButtons(self) -> None:
        self.btn_ok = QPushButton('Ok')
        self.btn_ok.clicked.connect(self.filterApply)

        self.btn_cancel = QPushButton('Сбросить')
        self.btn_cancel.clicked.connect(lambda: self.filterReset())

        self.btn_close = QPushButton('Закрыть')
        self.btn_close.clicked.connect(lambda: self.close())

    def setComboBoxes(self) -> None:
        self.combobox = QComboBox()
        self.combobox.setSizeAdjustPolicy(self.combobox.AdjustToMinimumContentsLengthWithIcon)
        self.combobox.setEditable(True)
        self.combobox.addItems(sorted(set(str(self.data))))
        self.combobox.setCurrentText('')

    def widgetRelation(self) -> None:
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
        point = QPoint(self.table.horizontalHeader().sectionViewportPosition(self.logicalIndex),
                       self.table.horizontalHeader().y())
        headerPos = self.table.horizontalHeader().mapTo(self.window, point)
        self.posX = headerPos.x()
        self.posY = headerPos.y() + self.table.horizontalHeader().height()

    def filterGeometry(self) -> None:
        self.setGeometry(self.posX, self.posY, self.table.columnWidth(self.logicalIndex), 0)
        self.setMinimumSize(self.table.columnWidth(self.logicalIndex), 0)
        self.setMaximumSize(200, 400)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.adjustSize()

    def filterReset(self) -> None:
        self.model.filters = self.proxy_filters
        self.model.invalidateFilter()
        self.model.setHeaderData(self.logicalIndex,
                                 Qt.Horizontal,
                                 QIcon(None),
                                 Qt.DecorationRole)
        self.combobox.setCurrentText('')
        self.table.resizeRowsToContents()
        self.close()

    def filterApply(self) -> None:
        if self.combobox.currentText() != '':
            regex_string = self.combobox.currentText()
            regex = QRegExp(f'{regex_string}')
            regex.setCaseSensitivity(Qt.CaseInsensitive)
        else:
            regex_data = []
            for key in self.cbs.keys():
                if self.cbs[key].isChecked():
                    regex_data.append(str(key))
            regex_string = '|'.join(regex_data)
            regex = QRegExp(f'^({regex_string})$')

        self.model.filters[self.logicalIndex] = regex
        self.model.invalidateFilter()
        self.model.setHeaderData(self.logicalIndex,
                                 Qt.Horizontal,
                                 CONFIG.style.filter,
                                 Qt.DecorationRole)
        self.table.resizeRowsToContents()
        self.close()
        self.window.updStatusBar()
