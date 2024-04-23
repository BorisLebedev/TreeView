""" Стартовое окно """

from __future__ import annotations

from typing import TYPE_CHECKING

import logging

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QComboBox
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QPushButton

from STC.gui.splash_screen import show_dialog

from STC.gui.windows.ancestors.window import WindowBasic

if TYPE_CHECKING:
    from STC.database.database import DbProduct


class WindowProductSelector(WindowBasic):
    """ Окно выбора изделия и методов обновления данных бд по сторонним источникам """

    showMainTable = pyqtSignal()
    syncWithExcel = pyqtSignal()
    syncWithExcelTdDb = pyqtSignal()
    syncWithPLM = pyqtSignal()
    newDocumentWindow = pyqtSignal()
    adminMK = pyqtSignal()

    def __init__(self, product_data: list[dict[str, int | str | DbProduct]]) -> None:
        logging.info('Инициализация окна выбора изделия')
        super().__init__()
        self.reverse = False
        self.product_data = product_data
        self.initUI()
        self.widgets()
        self.initDefaultValues()

    def initUI(self) -> None:
        """ Установка параметров окна выбора изделия """

        logging.info('Установка параметров окна выбора изделия')
        self.title = "Параметры новой таблицы"
        self.basic_layout.itemAt(0).widget().layout.itemAt(0).widget().setText(self.title)
        self.basic_layout.itemAt(0).widget().layout.itemAt(1).widget().setHidden(True)
        self.basic_layout.itemAt(0).widget().layout.itemAt(2).widget().setHidden(True)
        self.setGeometry(100, 100, 300, 400)
        self.setMinimumSize(300, 400)

    def initDefaultValues(self) -> None:
        """ Определяет начальные значения виджетов окна """

        self.itemsDeno()
        self.cb_deno.setCurrentText("")
        self.itemsName()
        self.cb_name.setCurrentText("")
        self.cb_name.setFocus()

    def itemsDeno(self) -> None:
        """ Определяет реакцию на изменение текста в
            виджете для наименования изделия.
            Формирует выпадающий список децимальных номеров изделий,
            у которых наименование содержит в себе текст
            из виджета для наименования изделия """

        self.cb_deno.blockSignals(True)
        self.cb_deno.clear()
        self.completer_list_deno = []
        self.cb_deno.clear()
        for product in self.product_data:
            if self.cb_name.currentText().lower() in product['name'].lower():
                self.completer_list_deno.append(product['denotation'])
        self.cb_deno.addItems(self.completer_list_deno)
        if self.cb_name.currentText() == '':
            self.cb_deno.setCurrentText("")
        self.cb_deno.blockSignals(False)

    def itemsName(self) -> None:
        """ Определяет реакцию на изменение текста в
            виджете для децимального номера.
            Формирует выпадающий список наименований изделий,
            у которых децимальный номер содержит в себе текст
            из виджета для децимального номера """

        self.cb_name.blockSignals(True)
        self.cb_name.clear()
        self.completer_list_name = []
        self.cb_name.clear()
        for product in self.product_data:
            if self.cb_deno.currentText().lower() in product['denotation'].lower():
                self.completer_list_name.append(product['name'])
        self.cb_name.addItems(sorted(self.completer_list_name))
        if self.cb_deno.currentText() == '':
            self.cb_name.setCurrentText("")
        self.cb_name.blockSignals(False)

    def widgets(self) -> None:
        """ Инициализация виджетов и их расположения """

        logging.info('Инициализация виджетов окна выбора изделия')

        label_deno = QLabel()
        label_deno.setText('Децимальный номер')

        self.cb_deno = QComboBox()
        self.cb_deno.setSizeAdjustPolicy(self.cb_deno.AdjustToMinimumContentsLengthWithIcon)
        self.cb_deno.setEditable(True)
        self.cb_deno.lineEdit().editingFinished.connect(self.itemsName)
        self.cb_deno.currentIndexChanged.connect(self.itemsName)

        label_name = QLabel()
        label_name.setText('Наименование')

        self.cb_name = QComboBox()
        self.cb_name.setSizeAdjustPolicy(self.cb_name.AdjustToMinimumContentsLengthWithIcon)
        self.cb_name.setEditable(True)
        self.cb_name.lineEdit().editingFinished.connect(self.itemsDeno)
        self.cb_name.currentIndexChanged.connect(self.itemsDeno)

        button = QPushButton()
        button.setText('Открыть изделие')
        button.clicked.connect(self.showMainTable)

        button_rev = QPushButton()
        button_rev.setText('Зависимые изделия')
        button_rev.clicked.connect(self.showMainTableReversed)

        button_new_product = QPushButton()
        button_new_product.setText('Новое изделие')
        button_new_product.clicked.connect(self.newDocumentWindow)

        button_excel = QPushButton()
        button_excel.setText('Загрузить составы Excel')
        button_excel.clicked.connect(self.syncWithExcel)

        button_excel_td_db = QPushButton()
        button_excel_td_db.setText('Загрузить данные ТД')
        button_excel_td_db.clicked.connect(self.syncWithExcelTdDb)

        button_excel_plm_db = QPushButton()
        button_excel_plm_db.setText('Обновить данные PLM')
        button_excel_plm_db.clicked.connect(self.syncWithPLM)

        button_admin = QPushButton()
        button_admin.setText('Администрирование МК')
        button_admin.clicked.connect(self.adminMK)

        self.main_layout.addWidget(label_name, 0, 0)
        self.main_layout.addWidget(self.cb_name, 1, 0)
        self.main_layout.addWidget(label_deno, 2, 0)

        self.main_layout.addWidget(self.cb_deno, 3, 0)
        self.main_layout.addWidget(button, 4, 0)
        self.main_layout.addWidget(button_rev, 5, 0)
        self.main_layout.addWidget(button_new_product, 6, 0)
        self.main_layout.addWidget(button_excel, 7, 0)
        self.main_layout.addWidget(button_excel_td_db, 8, 0)
        self.main_layout.addWidget(button_excel_plm_db, 9, 0)
        self.main_layout.addWidget(button_admin, 10, 0)

    def showMainTableReversed(self):
        """ Сингал, определяющий ориентацию построения
            иерархического древа изделия """

        self.reverse = True
        self.showMainTable.emit()

    @property
    def product_name(self):
        return self.cb_name.currentText()

    @property
    def product_deno(self):
        deno = self.cb_deno.currentText()
        if deno == '':
            show_dialog(text='Не указан децимальный номер')
        elif deno not in self.completer_list_deno:
            show_dialog(text=f'Не найдено изделие с децимальным номером {deno}')
            deno = ''
        return deno
